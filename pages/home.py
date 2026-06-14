"""Home Dashboard Page"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import func
from database.database import get_db
from services.document_service import DocumentService
from services.knowledge_service import KnowledgeService
from database.models import Employee, System, DocumentationGap


def show():
    st.title("📊 Executive Dashboard")
    st.markdown("### Organizational Knowledge Intelligence Overview")
    
    db = get_db()
    
    try:
        # Get statistics
        doc_stats = DocumentService.get_document_stats(db, user_id=st.session_state.user_id)
        knowledge_stats = KnowledgeService.get_knowledge_stats(db, user_id=st.session_state.user_id)
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Documents",
                doc_stats["total_documents"],
                f"{doc_stats['processed_documents']} processed"
            )
        
        with col2:
            st.metric(
                "Employees Tracked",
                knowledge_stats["total_employees"],
                f"{knowledge_stats['high_risk_employees']} high risk"
            )
        
        with col3:
            st.metric(
                "Systems Identified",
                knowledge_stats["total_systems"],
                f"{knowledge_stats['critical_systems']} critical"
            )
        
        with col4:
            st.metric(
                "Documentation Gaps",
                knowledge_stats["documentation_gaps"],
                "Need attention"
            )
        
        st.markdown("---")
        
        # Charts row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Risk Distribution")
            
            # Get risk distribution
            risk_data = db.query(
                Employee.risk_level,
                func.count(Employee.id)
            ).filter(
                Employee.risk_level.isnot(None),
                Employee.user_id == st.session_state.user_id
            ).group_by(Employee.risk_level).all()
            
            if risk_data:
                risk_levels = [r[0] for r in risk_data]
                risk_counts = [r[1] for r in risk_data]
                
                colors = {
                    'critical': '#dc3545',
                    'high': '#fd7e14',
                    'medium': '#ffc107',
                    'low': '#28a745'
                }
                
                fig = go.Figure(data=[go.Pie(
                    labels=risk_levels,
                    values=risk_counts,
                    marker=dict(colors=[colors.get(r, '#6c757d') for r in risk_levels]),
                    hole=0.4
                )])
                
                fig.update_layout(
                    title="Employee Risk Levels",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No risk data available yet. Upload documents to generate insights.")
        
        with col2:
            st.subheader("📊 File Type Distribution")
            
            if doc_stats["file_type_distribution"]:
                file_types = list(doc_stats["file_type_distribution"].keys())
                counts = list(doc_stats["file_type_distribution"].values())
                
                fig = go.Figure(data=[go.Bar(
                    x=file_types,
                    y=counts,
                    marker_color='#0d6efd'
                )])
                
                fig.update_layout(
                    title="Documents by File Type",
                    xaxis_title="File Type",
                    yaxis_title="Count",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No documents uploaded yet.")
        
        st.markdown("---")
        
        # Charts row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚠️ Top 10 High-Risk Employees")
            
            high_risk_employees = db.query(Employee).filter(
                Employee.dependency_score.isnot(None),
                Employee.user_id == st.session_state.user_id
            ).order_by(
                Employee.dependency_score.desc()
            ).limit(10).all()
            
            if high_risk_employees:
                names = [emp.name for emp in high_risk_employees]
                scores = [emp.dependency_score for emp in high_risk_employees]
                risk_levels = [emp.risk_level or 'unknown' for emp in high_risk_employees]
                
                # Color mapping
                color_map = {
                    'critical': '#dc3545',
                    'high': '#fd7e14',
                    'medium': '#ffc107',
                    'low': '#28a745',
                    'unknown': '#6c757d'
                }
                colors = [color_map.get(r, '#6c757d') for r in risk_levels]
                
                fig = go.Figure(data=[go.Bar(
                    y=names,
                    x=scores,
                    orientation='h',
                    marker_color=colors,
                    text=scores,
                    texttemplate='%{text:.1f}',
                    textposition='outside'
                )])
                
                fig.update_layout(
                    title="Dependency Scores",
                    xaxis_title="Risk Score",
                    yaxis_title="Employee",
                    height=400,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=50, t=50, b=50),
                    xaxis=dict(range=[0, 110]),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No employee data available. Run risk analysis to generate insights.")
        
        with col2:
            st.subheader("🔧 Critical Systems")
            
            critical_systems = db.query(System).filter(
                System.user_id == st.session_state.user_id
            ).order_by(
                System.mention_count.desc()
            ).limit(10).all()
            
            if critical_systems:
                system_names = [sys.name for sys in critical_systems]
                mention_counts = [sys.mention_count for sys in critical_systems]
                
                fig = go.Figure(data=[go.Bar(
                    y=system_names,
                    x=mention_counts,
                    orientation='h',
                    marker_color='#6610f2',
                    text=mention_counts,
                    textposition='outside'
                )])
                
                fig.update_layout(
                    title="Most Mentioned Systems",
                    xaxis_title="Mention Count",
                    yaxis_title="System",
                    height=400,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=50, t=50, b=50),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No system data available yet.")
        
        st.markdown("---")
        
        # Documentation Gaps
        st.subheader("📋 Critical Documentation Gaps")
        
        gaps = db.query(DocumentationGap).filter(
            DocumentationGap.status == "open",
            DocumentationGap.severity.in_(["high", "critical"]),
            DocumentationGap.user_id == st.session_state.user_id
        ).order_by(
            DocumentationGap.priority.desc()
        ).limit(5).all()
        
        if gaps:
            for gap in gaps:
                severity_color = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }
                
                with st.expander(
                    f"{severity_color.get(gap.severity, '⚪')} {gap.subject_name} - {gap.gap_type.replace('_', ' ').title()}"
                ):
                    st.write(f"**Type:** {gap.subject_type}")
                    st.write(f"**Severity:** {gap.severity}")
                    st.write(f"**Impact:** {gap.impact_description}")
                    st.write(f"**Recommendation:** {gap.recommendation}")
                    st.write(f"**Priority:** {gap.priority}/5")
        else:
            st.success("No critical documentation gaps identified!")
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📤 Upload Documents", use_container_width=True):
                st.switch_page("pages/upload_center.py")
        
        with col2:
            if st.button("🌐 View Knowledge Graph", use_container_width=True):
                st.switch_page("pages/knowledge_graph.py")
        
        with col3:
            if st.button("⚠️ Run Risk Analysis", use_container_width=True):
                st.switch_page("pages/risk_analysis.py")
        
        with col4:
            if st.button("🚨 Exit Simulator", use_container_width=True):
                st.switch_page("pages/exit_simulator.py")
    
    finally:
        db.close()
