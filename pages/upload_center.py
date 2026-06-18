"""Document Upload Center Page"""
import streamlit as st
from pathlib import Path
from datetime import datetime
import uuid
from sqlalchemy import func

from database.database import get_db
from database.models import KnowledgeEntity
from services.document_service import DocumentService
from utils.security import validate_file_upload, sanitize_filename
import config


def show():
    st.title("📤 Document Upload Center")
    st.markdown("Upload company documents for AI analysis and knowledge extraction")
    
    # Check if AI is available
    import config
    if not config.GROQ_API_KEY:
        st.warning("⚠️ GROQ_API_KEY not configured. Documents will be uploaded but AI entity extraction will be limited. Configure the API key in Settings → Secrets for full functionality.")
    
    # Upload section
    st.subheader("Upload New Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['csv', 'xlsx', 'pdf', 'docx', 'txt', 'md'],
            accept_multiple_files=True,
            help="Upload company documents including SOPs, meeting notes, project docs, etc."
        )
    
    with col2:
        category = st.selectbox(
            "Category",
            ["General", "SOP", "Meeting Notes", "Project Documentation", 
             "Incident Reports", "Client Documents", "Email", "Knowledge Base"]
        )
        
        tags_input = st.text_input("Tags (comma-separated)", help="e.g., hr, engineering, finance")
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")
        
        if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
            db = get_db()
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                uploaded_count = 0
                failed_count = 0
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"⏳ Uploading {uploaded_file.name}...")
                    
                    try:
                        # Validate file
                        is_valid, error_msg = validate_file_upload(
                            uploaded_file.name,
                            uploaded_file.size
                        )
                        
                        if not is_valid:
                            st.error(f"❌ {uploaded_file.name}: {error_msg}")
                            failed_count += 1
                            continue
                        
                        # Save file
                        filename = sanitize_filename(uploaded_file.name)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = config.UPLOAD_DIR / unique_filename
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Show 100% upload and proceed status
                        status_text.text(f"📤 {uploaded_file.name} - Uploaded 100%. Proceeding to process...")
                        
                        # Process tags
                        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                        
                        # Progress callback to show detailed percentage stages
                        current_pct = [0]
                        def progress_cb(percent, stage_text):
                            import time
                            start_val = current_pct[0]
                            for p in range(start_val + 1, percent + 1):
                                status_text.text(f"⏳ {uploaded_file.name} - Processing... {p}% ({stage_text})")
                                time.sleep(0.03)
                            current_pct[0] = percent
                        
                        # Upload to database and process
                        document = DocumentService.upload_document(
                            db=db,
                            file_path=str(file_path),
                            original_filename=uploaded_file.name,
                            user_id=st.session_state.user_id,
                            category=category if category != "General" else None,
                            tags=tags,
                            progress_callback=progress_cb
                        )
                        
                        uploaded_count += 1
                        st.success(f"✅ {uploaded_file.name} uploaded and processed successfully (100% complete)!")
                        
                        # Show transition to next
                        if idx + 1 < len(uploaded_files):
                            status_text.text(f"🎉 {uploaded_file.name} complete! Proceeding to next file...")
                    
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                        failed_count += 1
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
                
                st.markdown("---")
                st.success(f"**Upload Summary:** {uploaded_count} succeeded, {failed_count} failed")
                
                if uploaded_count > 0:
                    st.info("💡 Documents have been processed and indexed for semantic search. Visit the Knowledge Graph or Risk Analysis pages to see insights.")
            
            finally:
                db.close()
    
    st.markdown("---")
    
    # Recent uploads
    st.subheader("📋 Recent Uploads")
    
    db = get_db()
    try:
        recent_docs = DocumentService.get_documents(
            db=db,
            user_id=st.session_state.user_id if st.session_state.user_role != "admin" else None,
            limit=10
        )
        
        if recent_docs:
            for doc in recent_docs:
                with st.expander(
                    f"📄 {doc.original_filename} - {doc.upload_date.strftime('%Y-%m-%d %H:%M')}"
                ):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Type:** {doc.file_type}")
                        st.write(f"**Size:** {doc.file_size / 1024:.1f} KB")
                    
                    with col2:
                        st.write(f"**Category:** {doc.category or 'General'}")
                        st.write(f"**Status:** {'✅ Processed' if doc.is_processed else '⏳ Processing'}")
                    
                    with col3:
                        st.write(f"**Words:** {doc.word_count or 'N/A'}")
                        if doc.tags:
                            st.write(f"**Tags:** {', '.join(doc.tags)}")
                    
                    if doc.is_processed:
                        # Show entities
                        entities = db.query(func.count(KnowledgeEntity.id)).filter(
                            KnowledgeEntity.document_id == doc.id
                        ).scalar()
                        
                        if entities:
                            st.write(f"**Extracted Entities:** {entities}")
        else:
            st.info("No documents uploaded yet. Upload your first document above!")
    
    finally:
        db.close()
    
    st.markdown("---")
    
    # Upload guidelines
    with st.expander("📖 Upload Guidelines"):
        st.markdown("""
        ### Supported File Types
        - **CSV/XLSX**: Employee records, data exports
        - **PDF**: SOPs, reports, presentations
        - **DOCX**: Documentation, meeting notes
        - **TXT/MD**: Plain text documents, markdown files
        
        ### Best Practices
        - Use descriptive filenames
        - Categorize documents appropriately
        - Add relevant tags for better organization
        - Include employee names, systems, and processes in documents
        - Upload related documents together
        
        ### What Gets Extracted
        - Employee names and roles
        - Systems and technologies
        - Projects and initiatives
        - Business processes
        - Client information
        - Knowledge dependencies
        
        ### File Size Limit
        Maximum file size: **100 MB** per file
        """)
