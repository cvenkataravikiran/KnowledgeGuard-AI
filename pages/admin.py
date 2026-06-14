"""Admin Panel Page"""
import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import func
from database.database import get_db
from database.models import User, AuditLog, Document
from utils.security import hash_password, check_permission
import plotly.graph_objects as go


def show():
    st.title("👑 Admin Panel")
    st.markdown("System administration and user management")
    
    # Check admin permission
    if st.session_state.user_role != "admin":
        st.error("⛔ Access Denied: Admin privileges required")
        return
    
    tabs = st.tabs(["👥 Users", "📝 Audit Logs", "📊 Analytics"])
    
    # Users Tab
    with tabs[0]:
        st.subheader("User Management")
        
        db = get_db()
        try:
            # Create new user
            with st.expander("➕ Create New User"):
                with st.form("create_user_form"):
                    username = st.text_input("Username")
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    full_name = st.text_input("Full Name")
                    role = st.selectbox("Role", ["user", "manager", "admin"])
                    
                    if st.form_submit_button("Create User"):
                        if not all([username, email, password]):
                            st.error("Please fill in all required fields")
                        else:
                            # Check if user exists
                            existing = db.query(User).filter(
                                (User.username == username) | (User.email == email)
                            ).first()
                            
                            if existing:
                                st.error("Username or email already exists")
                            else:
                                new_user = User(
                                    username=username,
                                    email=email,
                                    hashed_password=hash_password(password),
                                    full_name=full_name,
                                    role=role,
                                    is_active=True,
                                    created_at=datetime.utcnow()
                                )
                                db.add(new_user)
                                db.commit()
                                st.success(f"✅ User {username} created successfully!")
                                st.rerun()
            
            st.markdown("---")
            
            # List users
            st.markdown("**All Users**")
            
            users = db.query(User).order_by(User.created_at.desc()).all()
            
            for user in users:
                with st.expander(
                    f"{'🟢' if user.is_active else '🔴'} {user.username} - {user.role}"
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Email:** {user.email}")
                        st.write(f"**Full Name:** {user.full_name or 'N/A'}")
                        st.write(f"**Role:** {user.role}")
                        st.write(f"**Status:** {'Active' if user.is_active else 'Inactive'}")
                        st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d')}")
                        if user.last_login:
                            st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Count documents
                        doc_count = db.query(Document).filter(
                            Document.uploaded_by == user.id
                        ).count()
                        st.write(f"**Documents Uploaded:** {doc_count}")
                    
                    with col2:
                        if user.id != st.session_state.user_id:  # Can't modify own account
                            if user.is_active:
                                if st.button("🚫 Deactivate", key=f"deactivate_{user.id}"):
                                    user.is_active = False
                                    db.commit()
                                    st.success(f"User {user.username} deactivated")
                                    st.rerun()
                            else:
                                if st.button("✅ Activate", key=f"activate_{user.id}"):
                                    user.is_active = True
                                    db.commit()
                                    st.success(f"User {user.username} activated")
                                    st.rerun()
                            
                            # Change role
                            new_role = st.selectbox(
                                "Change Role",
                                ["user", "manager", "admin"],
                                index=["user", "manager", "admin"].index(user.role),
                                key=f"role_{user.id}"
                            )
                            
                            if new_role != user.role:
                                if st.button("Update Role", key=f"update_{user.id}"):
                                    user.role = new_role
                                    db.commit()
                                    st.success(f"Role updated to {new_role}")
                                    st.rerun()
        
        finally:
            db.close()
    
    # Audit Logs Tab
    with tabs[1]:
        st.subheader("Audit Logs")
        
        db = get_db()
        try:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                action_filter = st.selectbox(
                    "Action",
                    ["All", "login", "upload", "delete", "update", "analyze"]
                )
            
            with col2:
                days_back = st.selectbox("Time Range", [1, 7, 30, 90, 365])
            
            with col3:
                limit = st.selectbox("Limit", [50, 100, 200, 500])
            
            # Query logs
            query = db.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
            
            if action_filter != "All":
                query = query.filter(AuditLog.action == action_filter)
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(AuditLog.created_at >= cutoff_date)
            
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
            
            st.markdown(f"**Showing {len(logs)} log entries**")
            
            if logs:
                for log in logs:
                    status_icon = "✅" if log.status == "success" else "❌" if log.status == "failure" else "⚠️"
                    
                    user = db.query(User).filter(User.id == log.user_id).first()
                    username = user.username if user else "System"
                    
                    with st.expander(
                        f"{status_icon} {log.action} by {username} - "
                        f"{log.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    ):
                        st.write(f"**Action:** {log.action}")
                        st.write(f"**User:** {username}")
                        st.write(f"**Resource:** {log.resource_type} (ID: {log.resource_id})")
                        st.write(f"**Status:** {log.status}")
                        
                        if log.description:
                            st.write(f"**Description:** {log.description}")
                        
                        if log.error_message:
                            st.error(f"**Error:** {log.error_message}")
                        
                        if log.ip_address:
                            st.write(f"**IP Address:** {log.ip_address}")
            else:
                st.info("No audit logs found for the selected criteria")
        
        finally:
            db.close()
    
    # Analytics Tab
    with tabs[2]:
        st.subheader("System Analytics")
        
        db = get_db()
        try:
            # User activity
            st.markdown("**User Activity (Last 30 Days)**")
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            user_activity = db.query(
                User.username,
                func.count(Document.id).label("doc_count")
            ).join(
                Document, User.id == Document.uploaded_by, isouter=True
            ).filter(
                Document.upload_date >= cutoff_date
            ).group_by(User.username).all()
            
            if user_activity:
                usernames = [ua[0] for ua in user_activity]
                doc_counts = [ua[1] for ua in user_activity]
                
                fig = go.Figure(data=[
                    go.Bar(x=usernames, y=doc_counts, marker_color='#0d6efd')
                ])
                
                fig.update_layout(
                    title="Documents Uploaded by User",
                    xaxis_title="User",
                    yaxis_title="Document Count",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # System metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                st.metric("Total Users", total_users, f"{active_users} active")
            
            with col2:
                from services.document_service import DocumentService
                doc_stats = DocumentService.get_document_stats(db)
                st.metric("Total Documents", doc_stats["total_documents"])
            
            with col3:
                recent_logins = db.query(User).filter(
                    User.last_login >= datetime.utcnow() - timedelta(days=7)
                ).count()
                st.metric("Active Users (7d)", recent_logins)
        
        finally:
            db.close()
