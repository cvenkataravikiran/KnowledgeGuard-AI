"""Employee Exit Simulator Page - Flagship Feature"""
import streamlit as st
import plotly.graph_objects as go
from database.database import get_db
from database.models import Employee, RiskAssessment, EmployeeMapping
from services.knowledge_service import KnowledgeService


def show():
    st.title("🚨 Employee Exit Simulator")
    st.markdown("### What-If Scenario Planning: Simulate employee departure impact")
    
    st.info("💡 **Flagship Feature**: Simulate the organizational impact if a key employee leaves")
    
    db = get_db()
    
    try:
        # Get all employees
        employees = db.query(Employee).filter(Employee.user_id == st.session_state.user_id).order_by(Employee.name).all()
        
        if not employees:
            st.warning("No employees found. Upload documents and run risk analysis first.")
            
            if st.button("📤 Go to Upload Center"):
                st.switch_page("pages/upload_center.py")
            
            return
        
        # Employee selection
        st.subheader("Select Employee")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            employee_names = [emp.name for emp in employees]
            selected_name = st.selectbox(
                "Choose an employee to simulate their exit",
                employee_names,
                help="Select an employee to see the impact if they leave the organization"
            )
        
        with col2:
            if st.button("🔄 Recalculate Impact", type="primary", use_container_width=True):
                employee = db.query(Employee).filter(Employee.name == selected_name, Employee.user_id == st.session_state.user_id).first()
                if employee:
                    with st.spinner("Analyzing impact..."):
                        KnowledgeService.calculate_employee_risk(db, employee.id, user_id=st.session_state.user_id)
                    st.success("Impact analysis updated!")
                    st.rerun()
        
        # Get selected employee
        selected_employee = db.query(Employee).filter(Employee.name == selected_name, Employee.user_id == st.session_state.user_id).first()
        
        if not selected_employee:
            st.error("Employee not found")
            return
        
        st.markdown("---")
        
        # Exit impact simulation
        st.subheader(f"📊 Impact Analysis: {selected_employee.name}")
        
        # Get risk assessment
        assessment = db.query(RiskAssessment).filter(
            RiskAssessment.employee_id == selected_employee.id,
            RiskAssessment.user_id == st.session_state.user_id
        ).order_by(RiskAssessment.assessed_at.desc()).first()
        
        if not assessment:
            st.warning("No risk assessment found. Click 'Recalculate Impact' to generate analysis.")
            return
        
        # Risk overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_color = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }
            st.metric(
                "Risk Level",
                f"{risk_color.get(assessment.risk_level or 'unknown', '⚪')} {(assessment.risk_level or 'unknown').upper()}"
            )
        
        with col2:
            st.metric(
                "Risk Score",
                f"{assessment.overall_risk_score:.1f}/100"
            )
        
        with col3:
            st.metric(
                "Knowledge Coverage",
                f"{assessment.knowledge_coverage_percent:.1f}%"
            )
        
        with col4:
            st.metric(
                "Recovery Time",
                f"{assessment.recovery_estimate_days} days"
            )
        
        # Risk score visualization
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=assessment.overall_risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Risk Score"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgreen"},
                    {'range': [40, 60], 'color': "yellow"},
                    {'range': [60, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed impact breakdown
        st.subheader("⚠️ If This Employee Leaves:")
        
        # Affected systems
        if assessment.affected_systems:
            with st.expander(f"🔧 Affected Systems ({len(assessment.affected_systems)})", expanded=True):
                st.markdown(f"**Critical Systems at Risk:** {len(assessment.affected_systems)}")
                
                for idx, system in enumerate(assessment.affected_systems[:15], 1):
                    st.write(f"{idx}. {system}")
                
                if len(assessment.affected_systems) > 15:
                    st.write(f"... and {len(assessment.affected_systems) - 15} more")
        
        # Affected projects
        if assessment.affected_projects:
            with st.expander(f"📋 Affected Projects ({len(assessment.affected_projects)})", expanded=True):
                st.markdown(f"**Projects at Risk:** {len(assessment.affected_projects)}")
                
                for idx, project in enumerate(assessment.affected_projects[:15], 1):
                    st.write(f"{idx}. {project}")
                
                if len(assessment.affected_projects) > 15:
                    st.write(f"... and {len(assessment.affected_projects) - 15} more")
        
        # Affected processes
        if assessment.affected_processes:
            with st.expander(f"⚙️ Affected Processes ({len(assessment.affected_processes)})", expanded=True):
                st.markdown(f"**Business Processes at Risk:** {len(assessment.affected_processes)}")
                
                for idx, process in enumerate(assessment.affected_processes[:15], 1):
                    st.write(f"{idx}. {process}")
                
                if len(assessment.affected_processes) > 15:
                    st.write(f"... and {len(assessment.affected_processes) - 15} more")
        
        st.markdown("---")
        
        # Risk breakdown
        st.subheader("📊 Risk Breakdown")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "System Dependency",
                f"{assessment.system_dependency_score:.1f}/100"
            )
            st.progress(assessment.system_dependency_score / 100)
        
        with col2:
            st.metric(
                "Process Dependency",
                f"{assessment.process_dependency_score:.1f}/100"
            )
            st.progress(assessment.process_dependency_score / 100)
        
        with col3:
            st.metric(
                "Project Dependency",
                f"{assessment.project_dependency_score:.1f}/100"
            )
            st.progress(assessment.project_dependency_score / 100)
        
        # Bar chart of risk components
        fig = go.Figure(data=[
            go.Bar(
                x=['System', 'Process', 'Project'],
                y=[
                    assessment.system_dependency_score,
                    assessment.process_dependency_score,
                    assessment.project_dependency_score
                ],
                marker_color=['#6610f2', '#0dcaf0', '#0d6efd'],
                text=[
                    f"{assessment.system_dependency_score:.1f}",
                    f"{assessment.process_dependency_score:.1f}",
                    f"{assessment.project_dependency_score:.1f}"
                ],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Risk Component Scores",
            xaxis_title="Component",
            yaxis_title="Score (0-100)",
            height=350,
            yaxis=dict(range=[0, 110]),
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Knowledge coverage
        st.subheader("📚 Knowledge Coverage Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if assessment.documented_areas:
                st.markdown("**✅ Well-Documented Areas:**")
                for area in assessment.documented_areas[:10]:
                    st.write(f"- {area}")
        
        with col2:
            if assessment.undocumented_areas:
                st.markdown("**❌ Poorly Documented Areas:**")
                for area in assessment.undocumented_areas[:10]:
                    st.write(f"- {area}")
        
        st.markdown("---")
        
        # Recommendations
        st.subheader("💡 Recommended Actions")
        
        if assessment.recommendations:
            for idx, rec in enumerate(assessment.recommendations, 1):
                st.info(f"**{idx}.** {rec}")
        else:
            st.success("No specific recommendations at this time.")
        
        st.markdown("---")
        
        # Recovery planning
        st.subheader("🔄 Recovery Planning")
        
        st.markdown(f"""
        **Estimated Recovery Timeline:** {assessment.recovery_estimate_days} days
        
        **Mitigation Steps:**
        1. **Immediate (Day 1-3):**
           - Initiate knowledge transfer sessions
           - Document critical procedures
           - Assign interim responsibilities
        
        2. **Short-term (Week 1-2):**
           - Conduct comprehensive handover
           - Create detailed documentation
           - Train backup personnel
        
        3. **Medium-term (Month 1):**
           - Hire replacement if needed
           - Complete knowledge transfer
           - Validate system access and ownership
        
        4. **Long-term (Month 2-3):**
           - Monitor system stability
           - Update documentation
           - Cross-train team members
        """)
        
        st.markdown("---")
        
        # Additional context
        with st.expander("📋 Employee Details"):
            st.write(f"**Name:** {selected_employee.name}")
            st.write(f"**Department:** {selected_employee.department or 'N/A'}")
            st.write(f"**Role:** {selected_employee.role or 'N/A'}")
            st.write(f"**Email:** {selected_employee.email or 'N/A'}")
            
            st.markdown("**Statistics:**")
            st.write(f"- Mentioned in {selected_employee.document_count} documents")
            st.write(f"- Associated with {selected_employee.system_count} systems")
            st.write(f"- Involved in {selected_employee.process_count} processes")
            st.write(f"- Working on {selected_employee.project_count} projects")
        
        # Export report
        st.markdown("---")
        
        if st.button("📄 Export Full Report", use_container_width=True):
            report = f"""
# Employee Exit Impact Report
## Employee: {selected_employee.name}

### Executive Summary
- **Risk Level:** {(assessment.risk_level or 'unknown').upper()}
- **Risk Score:** {assessment.overall_risk_score:.1f}/100
- **Knowledge Coverage:** {assessment.knowledge_coverage_percent:.1f}%
- **Estimated Recovery:** {assessment.recovery_estimate_days} days

### Affected Systems
{chr(10).join(f"- {sys}" for sys in (assessment.affected_systems or []))}

### Affected Projects
{chr(10).join(f"- {proj}" for proj in (assessment.affected_projects or []))}

### Affected Processes
{chr(10).join(f"- {proc}" for proc in (assessment.affected_processes or []))}

### Recommendations
{chr(10).join(f"{i}. {rec}" for i, rec in enumerate(assessment.recommendations or [], 1))}

---
Report generated by KnowledgeGuard AI
"""
            
            st.download_button(
                label="💾 Download Report",
                data=report,
                file_name=f"exit_report_{selected_employee.name.replace(' ', '_')}.md",
                mime="text/markdown"
            )
    
    finally:
        db.close()
