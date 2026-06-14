"""Settings Page"""
import streamlit as st
from database.database import get_db, backup_database, optimize_database
from database.models import User
from utils.security import hash_password, verify_password
from utils.embedding_manager import embedding_manager
import config


def show():
    st.title("⚙️ Settings")
    st.markdown("Configure application settings and preferences")
    
    tabs = st.tabs(["👤 Profile", "🔒 Security", "💾 Backup", "📊 System"])
    
    # Profile Tab
    with tabs[0]:
        st.subheader("User Profile")
        
        db = get_db()
        try:
            user = db.query(User).filter(User.id == st.session_state.user_id).first()
            
            if user:
                with st.form("profile_form"):
                    full_name = st.text_input("Full Name", value=user.full_name or "")
                    email = st.text_input("Email", value=user.email)
                    
                    if st.form_submit_button("Update Profile"):
                        user.full_name = full_name
                        user.email = email
                        db.commit()
                        st.success("✅ Profile updated successfully!")
                
                st.markdown("---")
                
                st.markdown("**Account Information**")
                st.write(f"**Username:** {user.username}")
                st.write(f"**Role:** {user.role}")
                st.write(f"**Account Created:** {user.created_at.strftime('%Y-%m-%d')}")
                if user.last_login:
                    st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M')}")
        
        finally:
            db.close()
    
    # Security Tab
    with tabs[1]:
        st.subheader("Change Password")
        
        with st.form("password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if not all([current_password, new_password, confirm_password]):
                    st.error("❌ Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    db = get_db()
                    try:
                        user = db.query(User).filter(User.id == st.session_state.user_id).first()
                        
                        if user and verify_password(current_password, user.hashed_password):
                            user.hashed_password = hash_password(new_password)
                            db.commit()
                            st.success("✅ Password changed successfully!")
                        else:
                            st.error("❌ Current password is incorrect")
                    finally:
                        db.close()
    
    # Backup Tab
    with tabs[2]:
        st.subheader("Database Backup & Recovery")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Create Backup**")
            st.write("Create a backup of the entire database including all documents and settings.")
            
            if st.button("💾 Create Backup Now", use_container_width=True):
                try:
                    backup_path = backup_database()
                    st.success(f"✅ Backup created successfully!")
                    st.info(f"📁 Backup location: {backup_path}")
                except Exception as e:
                    st.error(f"❌ Backup failed: {str(e)}")
        
        with col2:
            st.markdown("**Optimize Database**")
            st.write("Optimize database for better performance.")
            
            if st.button("⚡ Optimize Database", use_container_width=True):
                try:
                    optimize_database()
                    st.success("✅ Database optimized successfully!")
                except Exception as e:
                    st.error(f"❌ Optimization failed: {str(e)}")
        
        st.markdown("---")
        
        st.markdown("**Backup Settings**")
        st.info(f"""
        - **Automatic Backup:** {'Enabled' if config.BACKUP_ENABLED else 'Disabled'}
        - **Backup Interval:** Every {config.BACKUP_INTERVAL_HOURS} hours
        - **Backup Location:** {config.BACKUP_DIR}
        """)
    
    # System Tab
    with tabs[3]:
        st.subheader("System Information")
        
        # Application info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Application**")
            st.write(f"**Name:** {config.APP_NAME}")
            st.write(f"**Version:** {config.APP_VERSION}")
            st.write(f"**Environment:** {config.ENVIRONMENT}")
        
        with col2:
            st.markdown("**Configuration**")
            st.write(f"**Max Upload Size:** {config.MAX_UPLOAD_SIZE_MB} MB")
            st.write(f"**Chunk Size:** {config.CHUNK_SIZE} chars")
            st.write(f"**Embedding Model:** {config.EMBEDDING_MODEL}")
        
        st.markdown("---")
        
        # Database stats
        st.subheader("📊 Database Statistics")
        
        db = get_db()
        try:
            from services.document_service import DocumentService
            from services.knowledge_service import KnowledgeService
            
            doc_stats = DocumentService.get_document_stats(db, user_id=st.session_state.user_id)
            knowledge_stats = KnowledgeService.get_knowledge_stats(db, user_id=st.session_state.user_id)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Documents", doc_stats["total_documents"])
                st.metric("Total Employees", knowledge_stats["total_employees"])
            
            with col2:
                st.metric("Total Systems", knowledge_stats["total_systems"])
                st.metric("Total Projects", knowledge_stats["total_projects"])
            
            with col3:
                st.metric("Database Size", f"{doc_stats['total_size_mb']} MB")
                st.metric("High Risk Employees", knowledge_stats["high_risk_employees"])
        
        finally:
            db.close()
        
        st.markdown("---")
        
        # Vector database stats
        st.subheader("🔍 Vector Database Statistics")
        
        index_stats = embedding_manager.get_index_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Vectors", index_stats["total_vectors"])
        
        with col2:
            st.metric("Dimension", index_stats["dimension"])
        
        with col3:
            st.metric("Active Documents", index_stats["active_documents"])
        
        st.markdown("---")
        
        # Danger zone
        if st.session_state.user_role == "admin":
            with st.expander("🚨 Danger Zone", expanded=False):
                st.error("**Warning:** These actions are irreversible!")
                
                st.markdown("**Rebuild Vector Index**")
                st.write("Rebuild the entire FAISS index from scratch. Use this if the index is corrupted.")
                
                if st.button("🔄 Rebuild Vector Index"):
                    with st.spinner("Rebuilding index..."):
                        db = get_db()
                        try:
                            from database.models import DocumentChunk
                            
                            chunks = db.query(DocumentChunk).all()
                            documents_data = [(chunk.content, {
                                "document_id": chunk.document_id,
                                "chunk_index": chunk.chunk_index
                            }) for chunk in chunks]
                            
                            embedding_manager.rebuild_index(documents_data)
                            st.success("✅ Vector index rebuilt successfully!")
                        except Exception as e:
                            st.error(f"❌ Rebuild failed: {str(e)}")
                        finally:
                            db.close()
