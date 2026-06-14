"""SQLAlchemy Database Models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User authentication and profile"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # admin, manager, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    documents = relationship("Document", back_populates="uploaded_by_user")
    chat_history = relationship("ChatHistory", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    """Uploaded documents"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    title = Column(String(255))
    description = Column(Text)
    category = Column(String(50))  # SOP, Meeting Notes, Project Docs, etc.
    tags = Column(JSON)  # List of tags
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    word_count = Column(Integer)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("KnowledgeEntity", back_populates="document")


class DocumentChunk(Base):
    """Chunked text from documents for semantic search"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(100))  # Reference to FAISS index
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class KnowledgeEntity(Base):
    """Extracted entities from documents"""
    __tablename__ = "knowledge_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)  # employee, system, process, client, technology
    entity_name = Column(String(255), nullable=False, index=True)
    context = Column(Text)  # Surrounding text
    confidence = Column(Float, default=1.0)
    mention_count = Column(Integer, default=1)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="entities")


class Employee(Base):
    """Employee profiles and knowledge mapping"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100))
    department = Column(String(100))
    role = Column(String(100))
    
    # Risk Metrics
    dependency_score = Column(Float, default=0.0)  # 0-100
    risk_level = Column(String(20))  # low, medium, high, critical
    knowledge_areas = Column(JSON)  # List of expertise areas
    
    # Statistics
    document_count = Column(Integer, default=0)
    system_count = Column(Integer, default=0)
    process_count = Column(Integer, default=0)
    project_count = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mappings = relationship("EmployeeMapping", back_populates="employee")
    risk_assessments = relationship("RiskAssessment", back_populates="employee")
    
    __table_args__ = (
        {"schema": None},
    )  # Allows same employee name for different users


class EmployeeMapping(Base):
    """Relationships between employees and various entities"""
    __tablename__ = "employee_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Relationship type and target
    mapping_type = Column(String(50), nullable=False)  # system, process, project, client
    target_name = Column(String(255), nullable=False)
    
    # Relationship strength
    strength = Column(Float, default=1.0)  # 0-1
    is_primary_owner = Column(Boolean, default=False)
    
    # Context
    evidence = Column(JSON)  # List of document IDs where relationship was found
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="mappings")


class Project(Base):
    """Project information"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(50))  # active, completed, on-hold
    
    # Ownership
    primary_owner = Column(String(100))
    team_members = Column(JSON)  # List of employee names
    
    # Documentation
    documentation_score = Column(Float, default=0.0)  # 0-100
    document_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {"schema": None},
    )  # Allows same project name for different users


class System(Base):
    """Systems and technologies"""
    __tablename__ = "systems"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    system_type = Column(String(50))  # application, infrastructure, database, api
    description = Column(Text)
    
    # Ownership
    primary_owner = Column(String(100))
    backup_owners = Column(JSON)  # List of employee names
    
    # Risk
    criticality = Column(String(20))  # low, medium, high, critical
    documentation_score = Column(Float, default=0.0)
    
    # Statistics
    mention_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {"schema": None},
    )  # Allows same system name for different users


class RiskAssessment(Base):
    """Risk assessments for employees"""
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Assessment Results
    overall_risk_score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Detailed Scores
    system_dependency_score = Column(Float, default=0.0)
    process_dependency_score = Column(Float, default=0.0)
    project_dependency_score = Column(Float, default=0.0)
    documentation_gap_score = Column(Float, default=0.0)
    
    # Impact Analysis
    affected_systems = Column(JSON)  # List of system names
    affected_projects = Column(JSON)
    affected_processes = Column(JSON)
    
    # Knowledge Coverage
    knowledge_coverage_percent = Column(Float, default=0.0)  # 0-100
    documented_areas = Column(JSON)
    undocumented_areas = Column(JSON)
    
    # Recommendations
    recommendations = Column(JSON)
    recovery_estimate_days = Column(Integer)
    
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="risk_assessments")


class ChatHistory(Base):
    """AI chat conversation history"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Conversation
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # Context
    source_documents = Column(JSON)  # List of document IDs used
    confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")


class AuditLog(Base):
    """Audit trail for all system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))  # document, employee, system, etc.
    resource_id = Column(Integer)
    
    # Details
    description = Column(Text)
    extra_data = Column(JSON)  # Additional action-specific data
    
    # Status
    status = Column(String(20))  # success, failure, warning
    error_message = Column(Text)
    
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class DocumentationGap(Base):
    """Identified documentation gaps"""
    __tablename__ = "documentation_gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    gap_type = Column(String(50), nullable=False)  # missing_sop, outdated, incomplete
    
    # Subject
    subject_type = Column(String(50))  # system, process, project
    subject_name = Column(String(255))
    
    # Assessment
    severity = Column(String(20))  # low, medium, high, critical
    impact_description = Column(Text)
    
    # Recommendations
    recommendation = Column(Text)
    priority = Column(Integer)  # 1-5
    
    # Status
    status = Column(String(20), default="open")  # open, in_progress, resolved
    assigned_to = Column(String(100))
    
    identified_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
