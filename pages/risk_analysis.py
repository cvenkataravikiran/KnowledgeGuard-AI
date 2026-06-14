"""Risk Analysis Page"""
import streamlit as st
import plotly.graph_objects as go
from database.database import get_db
from services.knowledge_service import KnowledgeService
from database.models import Employee, RiskAssessment


def show():
    st.title("⚠️ Risk Analysis")
    st.markdown("Identify and analyze organizational knowledge risks")
    
    db = get_db()
    
    try:
        # Sync data
        with st.spinner("Synchronizing knowledge data..."):
            KnowledgeService.sync_employees(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_systems(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_projects(db, user_id=st.session_state.user_id)
            KnowledgeService.sync_mappings(db, user_id=st.session_state.user_id)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Run Complete Risk Analysis", type="primary", use_container_width=True):
                employees = db.query(Employee).filter(Employee.user_id == st.session_state.user_id).all()
                
                if not employees:
                    st.warning("No employees found. Upload documents first.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, employee in enumerate(employees):
                        status_text.text(f"Analyzing {employee.name}...")
                        try:
                            KnowledgeService.calculate_employee_risk(db, employee.id, user_id=st.session_state.user_id)
                        except Exception as e:
                            st.error(f"Error analyzing {employee.name}: {str(e)}")
                        
                        progress_bar.progress((idx + 1) / len(employees))
                    
                    status_text.text("Analysis complete!")
                    st.success(f"✅ Risk analysis completed for {len(employees)} employees")
                    st.rerun()
        
        with col2:
            if st.button("📋 Analyze Documentation Gaps", use_container_width=True):
                gaps = KnowledgeService.analyze_documentation_gaps(db, user_id=st.session_state.user_id)
                st.success(f"✅ Identified {len(gaps)} documentation gaps")
                st.rerun()
        
        st.markdown("---")
        
        # Get employees
        employees = db.query(Employee).filter(Employee.user_id == st.session_state.user_id).order_by(
            Employee.dependency_score.desc()
        ).all()
        
        if not employees:
            st.info("No employee data available. Upload documents to get started.")
            return
        
        # Risk overview
        st.subheader("📊 Risk Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        critical_count = len([e for e in employees if e.risk_level == "critical"])
        high_count = len([e for e in employees if e.risk_level == "high"])
        medium_count = len([e for e in employees if e.risk_level == "medium"])
        low_count = len([e for e in employees if e.risk_level == "low" or e.risk_level is None])
        
        with col1:
            st.metric("🔴 Critical", critical_count)
        
        with col2:
            st.metric("🟠 High", high_count)
        
        with col3:
            st.metric("🟡 Medium", medium_count)
        
        with col4:
            st.metric("🟢 Low", low_count)
        
        # Risk distribution chart
        if any([critical_count, high_count, medium_count, low_count]):
            fig = go.Figure(data=[go.Pie(
                labels=['Critical', 'High', 'Medium', 'Low'],
                values=[critical_count, high_count, medium_count, low_count],
                marker=dict(colors=['#dc3545', '#fd7e14', '#ffc107', '#28a745']),
                hole=0.4
            )])
            
            fig.update_layout(
                title="Risk Level Distribution",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Employee risk table
        st.subheader("👥 Employee Risk Scores")
        
        # Filter
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            ["All", "Critical", "High", "Medium", "Low"]
        )
        
        filtered_employees = employees
        if risk_filter != "All":
            filtered_employees = [e for e in employees if e.risk_level == risk_filter.lower()]
        
        for employee in filtered_employees:
            risk_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }
            
            with st.expander(
                f"{risk_emoji.get(employee.risk_level or 'low', '⚪')} {employee.name} - "
                f"Risk Score: {employee.dependency_score:.1f}/100"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Department:** {employee.department or 'N/A'}")
                    st.write(f"**Role:** {employee.role or 'N/A'}")
                    st.write(f"**Email:** {employee.email or 'N/A'}")
                    
                    st.markdown("**Statistics:**")
                    st.write(f"- Documents: {employee.document_count}")
                    st.write(f"- Systems: {employee.system_count}")
                    st.write(f"- Processes: {employee.process_count}")
                    st.write(f"- Projects: {employee.project_count}")
                
                with col2:
                    st.metric("Risk Score", f"{employee.dependency_score:.1f}")
                    st.metric("Risk Level", (employee.risk_level or "unknown").upper())
                
                # Get latest assessment
                assessment = db.query(RiskAssessment).filter(
                    RiskAssessment.employee_id == employee.id,
                    RiskAssessment.user_id == st.session_state.user_id
                ).order_by(RiskAssessment.assessed_at.desc()).first()
                
                if assessment:
                    st.markdown("---")
                    
                    # Detailed scores
                    st.markdown("**Detailed Risk Breakdown:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("System Dependency", f"{assessment.system_dependency_score:.1f}")
                    
                    with col2:
                        st.metric("Process Dependency", f"{assessment.process_dependency_score:.1f}")
                    
                    with col3:
                        st.metric("Project Dependency", f"{assessment.project_dependency_score:.1f}")
                    
                    # Affected items
                    if assessment.affected_systems:
                        st.markdown("**Affected Systems:**")
                        for sys in assessment.affected_systems[:10]:
                            st.write(f"- {sys}")
                    
                    if assessment.affected_projects:
                        st.markdown("**Affected Projects:**")
                        for proj in assessment.affected_projects[:10]:
                            st.write(f"- {proj}")
                    
                    if assessment.affected_processes:
                        st.markdown("**Affected Processes:**")
                        for proc in assessment.affected_processes[:10]:
                            st.write(f"- {proc}")
                    
                    # Knowledge coverage
                    st.markdown(f"**Knowledge Coverage:** {assessment.knowledge_coverage_percent:.1f}%")
                    
                    progress_color = "green" if assessment.knowledge_coverage_percent >= 70 else \
                                   "orange" if assessment.knowledge_coverage_percent >= 40 else "red"
                    
                    st.progress(assessment.knowledge_coverage_percent / 100)
                    
                    # Recommendations
                    if assessment.recommendations:
                        st.markdown("**Recommendations:**")
                        for rec in assessment.recommendations:
                            st.write(f"✅ {rec}")
                    
                    st.write(f"**Estimated Recovery Time:** {assessment.recovery_estimate_days} days")
        
        st.markdown("---")
        
        # Documentation gaps
        st.subheader("📋 Documentation Gaps")
        
        from database.models import DocumentationGap
        
        gaps = db.query(DocumentationGap).filter(
            DocumentationGap.status == "open",
            DocumentationGap.user_id == st.session_state.user_id
        ).order_by(
            DocumentationGap.priority.desc()
        ).all()
        
        if gaps:
            for gap in gaps:
                severity_color = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                
                with st.expander(
                    f"{severity_color.get(gap.severity, '⚪')} {gap.subject_name} - "
                    f"{gap.gap_type.replace('_', ' ').title()}"
                ):
                    st.write(f"**Type:** {gap.subject_type}")
                    st.write(f"**Severity:** {gap.severity.upper()}")
                    st.write(f"**Priority:** {gap.priority}/5")
                    st.write(f"**Impact:** {gap.impact_description}")
                    st.markdown(f"**Recommendation:** {gap.recommendation}")
                    
                    if st.button(f"Mark as Resolved", key=f"resolve_{gap.id}"):
                        from datetime import datetime
                        gap.status = "resolved"
                        gap.resolved_at = datetime.utcnow()
                        db.commit()
                        st.success("Gap marked as resolved!")
                        st.rerun()
        else:
            st.info("No open documentation gaps. Run gap analysis to identify issues.")
    
    finally:
        db.close()
