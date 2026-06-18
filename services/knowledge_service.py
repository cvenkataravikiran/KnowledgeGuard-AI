"""Knowledge extraction and analysis service"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict

from database.models import (
    KnowledgeEntity, Employee, EmployeeMapping, Project, System,
    RiskAssessment, DocumentationGap, Document
)
from utils.ai_analyzer import ai_analyzer


class KnowledgeService:
    """Service for knowledge extraction and analysis"""
    
    @staticmethod
    def sync_employees(db: Session, user_id: int):
        """Sync employees from extracted entities for a specific user"""
        try:
            # Get all employee entities for the user's documents
            employee_entities = db.query(KnowledgeEntity).join(
                Document, KnowledgeEntity.document_id == Document.id
            ).filter(
                KnowledgeEntity.entity_type == "employees",
                Document.uploaded_by == user_id
            ).all()
            
            if not employee_entities:
                return
            
            # Group by employee name
            employee_mentions = defaultdict(list)
            for entity in employee_entities:
                employee_mentions[entity.entity_name].append(entity)
            
            # Create or update employee records
            for employee_name, entities in employee_mentions.items():
                employee = db.query(Employee).filter(
                    Employee.name == employee_name,
                    Employee.user_id == user_id
                ).first()
                
                if not employee:
                    employee = Employee(name=employee_name, user_id=user_id)
                    db.add(employee)
                
                # Update document count
                unique_docs = set(e.document_id for e in entities)
                employee.document_count = len(unique_docs)
            
            db.commit()
        except Exception as e:
            print(f"Error in sync_employees: {str(e)}")
            db.rollback()
    
    @staticmethod
    def sync_systems(db: Session, user_id: int):
        """Sync systems from extracted entities for a specific user"""
        try:
            system_entities = db.query(KnowledgeEntity).join(
                Document, KnowledgeEntity.document_id == Document.id
            ).filter(
                KnowledgeEntity.entity_type == "systems",
                Document.uploaded_by == user_id
            ).all()
            
            if not system_entities:
                return
            
            system_mentions = defaultdict(list)
            for entity in system_entities:
                system_mentions[entity.entity_name].append(entity)
            
            for system_name, entities in system_mentions.items():
                system = db.query(System).filter(
                    System.name == system_name,
                    System.user_id == user_id
                ).first()
                
                if not system:
                    system = System(name=system_name, user_id=user_id)
                    db.add(system)
                
                system.mention_count = len(entities)
                unique_docs = set(e.document_id for e in entities)
                system.document_count = len(unique_docs)
            
            db.commit()
        except Exception as e:
            print(f"Error in sync_systems: {str(e)}")
            db.rollback()
    
    @staticmethod
    def sync_projects(db: Session, user_id: int):
        """Sync projects from extracted entities for a specific user"""
        try:
            project_entities = db.query(KnowledgeEntity).join(
                Document, KnowledgeEntity.document_id == Document.id
            ).filter(
                KnowledgeEntity.entity_type == "projects",
                Document.uploaded_by == user_id
            ).all()
            
            if not project_entities:
                return
            
            project_mentions = defaultdict(list)
            for entity in project_entities:
                project_mentions[entity.entity_name].append(entity)
            
            for project_name, entities in project_mentions.items():
                project = db.query(Project).filter(
                    Project.name == project_name,
                    Project.user_id == user_id
                ).first()
                
                if not project:
                    project = Project(name=project_name, user_id=user_id)
                    db.add(project)
                
                unique_docs = set(e.document_id for e in entities)
                project.document_count = len(unique_docs)
            
            db.commit()
        except Exception as e:
            print(f"Error in sync_projects: {str(e)}")
            db.rollback()
            unique_docs = set(e.document_id for e in entities)
            project.document_count = len(unique_docs)
        
        db.commit()
    
    @staticmethod
    def build_knowledge_graph(db: Session, user_id: int) -> Dict:
        """Build knowledge graph data structure for a specific user"""
        nodes = []
        edges = []
        
        # Add employee nodes
        employees = db.query(Employee).filter(Employee.user_id == user_id).all()
        for emp in employees:
            nodes.append({
                "id": f"emp_{emp.id}",
                "label": emp.name,
                "type": "employee",
                "risk_level": emp.risk_level or "low",
                "size": 20 + (emp.dependency_score or 0) / 5
            })
        
        # Add system nodes
        systems = db.query(System).filter(System.user_id == user_id).all()
        for sys in systems:
            nodes.append({
                "id": f"sys_{sys.id}",
                "label": sys.name,
                "type": "system",
                "criticality": sys.criticality or "low",
                "size": 15 + (sys.mention_count or 0) / 10
            })
        
        # Add project nodes
        projects = db.query(Project).filter(Project.user_id == user_id).all()
        for proj in projects:
            nodes.append({
                "id": f"proj_{proj.id}",
                "label": proj.name,
                "type": "project",
                "status": proj.status or "active",
                "size": 12
            })
        
        # Add edges from mappings
        mappings = db.query(EmployeeMapping).filter(EmployeeMapping.user_id == user_id).all()
        for mapping in mappings:
            employee = db.query(Employee).filter(Employee.id == mapping.employee_id, Employee.user_id == user_id).first()
            if not employee:
                continue
            
            target_id = None
            if mapping.mapping_type == "system":
                sys = db.query(System).filter(System.name == mapping.target_name, System.user_id == user_id).first()
                if sys:
                    target_id = f"sys_{sys.id}"
            elif mapping.mapping_type == "project":
                proj = db.query(Project).filter(Project.name == mapping.target_name, Project.user_id == user_id).first()
                if proj:
                    target_id = f"proj_{proj.id}"
            
            if target_id:
                edges.append({
                    "from": f"emp_{employee.id}",
                    "to": target_id,
                    "type": mapping.mapping_type,
                    "strength": mapping.strength or 1.0,
                    "is_primary": mapping.is_primary_owner
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    @staticmethod
    def calculate_employee_risk(db: Session, employee_id: int, user_id: int) -> RiskAssessment:
        """Calculate risk score for an employee, isolated by user_id"""
        employee = db.query(Employee).filter(Employee.id == employee_id, Employee.user_id == user_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Get employee mappings
        mappings = db.query(EmployeeMapping).filter(
            EmployeeMapping.employee_id == employee_id,
            EmployeeMapping.user_id == user_id
        ).all()
        
        # Count dependencies
        system_mappings = [m for m in mappings if m.mapping_type == "system"]
        process_mappings = [m for m in mappings if m.mapping_type == "process"]
        project_mappings = [m for m in mappings if m.mapping_type == "project"]
        
        # Calculate scores (simplified version)
        system_score = min(len(system_mappings) * 15, 100)
        process_score = min(len(process_mappings) * 20, 100)
        project_score = min(len(project_mappings) * 10, 100)
        
        # Primary ownership bonus
        primary_count = len([m for m in mappings if m.is_primary_owner])
        primary_bonus = min(primary_count * 25, 50)
        
        # Overall score
        overall_score = min(
            (system_score + process_score + project_score + primary_bonus) / 3.5,
            100
        )
        
        # Determine risk level
        if overall_score >= 80:
            risk_level = "critical"
        elif overall_score >= 60:
            risk_level = "high"
        elif overall_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Get affected items
        affected_systems = [m.target_name for m in system_mappings]
        affected_projects = [m.target_name for m in project_mappings]
        affected_processes = [m.target_name for m in process_mappings]
        
        # Calculate knowledge coverage (based on documentation)
        total_areas = len(system_mappings) + len(process_mappings) + len(project_mappings)
        documented_count = len([m for m in mappings if m.evidence and len(m.evidence) >= 2])
        coverage = (documented_count / total_areas * 100) if total_areas > 0 else 0
        
        # Generate recommendations
        recommendations = []
        if overall_score >= 60:
            recommendations.append("Create detailed documentation for all owned systems")
            recommendations.append("Assign backup owners for critical systems")
            recommendations.append("Conduct knowledge transfer sessions")
        if coverage < 50:
            recommendations.append("Document standard operating procedures")
            recommendations.append("Record video tutorials for key processes")
        if primary_count > 3:
            recommendations.append("Distribute primary ownership responsibilities")
        
        # Create or update risk assessment
        assessment = db.query(RiskAssessment).filter(
            RiskAssessment.employee_id == employee_id,
            RiskAssessment.user_id == user_id
        ).order_by(RiskAssessment.assessed_at.desc()).first()
        
        if not assessment:
            assessment = RiskAssessment(employee_id=employee_id, user_id=user_id)
            db.add(assessment)
        
        assessment.overall_risk_score = overall_score
        assessment.risk_level = risk_level
        assessment.system_dependency_score = system_score
        assessment.process_dependency_score = process_score
        assessment.project_dependency_score = project_score
        assessment.affected_systems = affected_systems
        assessment.affected_projects = affected_projects
        assessment.affected_processes = affected_processes
        assessment.knowledge_coverage_percent = coverage
        assessment.recommendations = recommendations
        assessment.recovery_estimate_days = max(5, int(overall_score / 10))
        
        # Update employee
        employee.dependency_score = overall_score
        employee.risk_level = risk_level
        
        db.commit()
        db.refresh(assessment)
        
        return assessment
    
    @staticmethod
    def analyze_documentation_gaps(db: Session, user_id: int) -> List[DocumentationGap]:
        """Analyze and identify documentation gaps, isolated by user_id"""
        gaps = []
        
        # Check systems without sufficient documentation
        systems = db.query(System).filter(System.user_id == user_id).all()
        for system in systems:
            if system.document_count < 2:
                gap = DocumentationGap(
                    gap_type="missing_sop",
                    subject_type="system",
                    subject_name=system.name,
                    severity="high" if system.criticality == "critical" else "medium",
                    impact_description=f"System '{system.name}' has insufficient documentation",
                    recommendation="Create comprehensive system documentation including architecture, deployment, and troubleshooting guides",
                    priority=5 if system.criticality == "critical" else 3,
                    user_id=user_id
                )
                db.add(gap)
                gaps.append(gap)
        
        # Check projects without owners
        projects = db.query(Project).filter(
            Project.primary_owner == None,
            Project.user_id == user_id
        ).all()
        
        for project in projects:
            gap = DocumentationGap(
                gap_type="incomplete",
                subject_type="project",
                subject_name=project.name,
                severity="high",
                impact_description=f"Project '{project.name}' has no assigned owner",
                recommendation="Assign a primary project owner and document responsibilities",
                priority=4,
                user_id=user_id
            )
            db.add(gap)
            gaps.append(gap)
        
        db.commit()
        return gaps
    
    @staticmethod
    def sync_mappings(db: Session, user_id: int):
        """Sync employee mappings from entity co-occurrences in documents for a specific user"""
        try:
            # Delete existing mappings for this user to rebuild fresh
            db.query(EmployeeMapping).filter(EmployeeMapping.user_id == user_id).delete()
            
            # Get all processed documents for this user
            documents = db.query(Document).filter(
                Document.is_processed == True,
                Document.uploaded_by == user_id
            ).all()
            
            if not documents:
                db.commit()
                return
            
            for doc in documents:
                # Get all entities for this document
                entities = db.query(KnowledgeEntity).filter(
                    KnowledgeEntity.document_id == doc.id
                ).all()
                
                # Separate employees and other targets
                employees = [e for e in entities if e.entity_type == "employees"]
                targets = [e for e in entities if e.entity_type in ["systems", "projects", "processes"]]
                
                if not employees or not targets:
                    continue
                    
                ENTITY_TO_MAPPING_TYPE = {
                    "systems": "system",
                    "projects": "project",
                    "processes": "process"
                }
                
            for emp_entity in employees:
                # Find the employee record by name
                employee = db.query(Employee).filter(
                    Employee.name == emp_entity.entity_name,
                    Employee.user_id == user_id
                ).first()
                if not employee:
                    continue
                    
                for target_entity in targets:
                    mapping_type = ENTITY_TO_MAPPING_TYPE.get(target_entity.entity_type)
                    if not mapping_type:
                        continue
                        
                    # Check if mapping already exists
                    mapping = db.query(EmployeeMapping).filter(
                        EmployeeMapping.employee_id == employee.id,
                        EmployeeMapping.mapping_type == mapping_type,
                        EmployeeMapping.target_name == target_entity.entity_name,
                        EmployeeMapping.user_id == user_id
                    ).first()
                    
                    if not mapping:
                        mapping = EmployeeMapping(
                            employee_id=employee.id,
                            mapping_type=mapping_type,
                            target_name=target_entity.entity_name,
                            strength=0.5,
                            is_primary_owner=False,
                            evidence=[],
                            user_id=user_id
                        )
                        db.add(mapping)
                    
                    # Update evidence and strength
                    evidence = list(mapping.evidence or [])
                    if doc.id not in evidence:
                        evidence.append(doc.id)
                        mapping.evidence = evidence
                    
                    # Heuristic for primary owner
                    if emp_entity.mention_count >= 2:
                        mapping.is_primary_owner = True
                        mapping.strength = 1.0
                    else:
                        mapping.strength = min(1.0, 0.5 + (len(evidence) * 0.1))
            
            db.commit()
        except Exception as e:
            print(f"Error in sync_mappings: {str(e)}")
            db.rollback()
    
    @staticmethod
    def get_knowledge_stats(db: Session, user_id: int) -> Dict:
        """Get knowledge statistics for a user"""
        return {
            "total_employees": db.query(Employee).filter(Employee.user_id == user_id).count(),
            "total_systems": db.query(System).filter(System.user_id == user_id).count(),
            "total_projects": db.query(Project).filter(Project.user_id == user_id).count(),
            "high_risk_employees": db.query(Employee).filter(
                Employee.risk_level.in_(["high", "critical"]),
                Employee.user_id == user_id
            ).count(),
            "critical_systems": db.query(System).filter(
                System.criticality == "critical",
                System.user_id == user_id
            ).count(),
            "documentation_gaps": db.query(DocumentationGap).filter(
                DocumentationGap.status == "open",
                DocumentationGap.user_id == user_id
            ).count()
        }
