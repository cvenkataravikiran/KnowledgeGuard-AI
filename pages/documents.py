"""Documents Management Page"""
import streamlit as st
from database.database import get_db
from services.document_service import DocumentService
from database.models import Document, KnowledgeEntity


def show():
    st.title("📚 Document Management")
    st.markdown("View, search, and manage uploaded documents")
    
    db = get_db()
    
    try:
        # Search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("🔍 Search documents", placeholder="Search by filename or content...")
        
        with col2:
            category_filter = st.selectbox(
                "Category",
                ["All", "SOP", "Meeting Notes", "Project Documentation", 
                 "Incident Reports", "Client Documents", "Email", "Knowledge Base"]
            )
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Name", "Size"])
        
        # Get documents
        if search_query:
            # Semantic search
            search_results = DocumentService.search_documents(search_query, user_id=st.session_state.user_id, db=db, top_k=20)
            st.info(f"Found {len(search_results)} relevant documents")
            
            # Display search results
            for result in search_results:
                doc = db.query(Document).filter(Document.id == result["document_id"]).first()
                if doc:
                    with st.expander(
                        f"📄 {doc.original_filename} - Relevance: {result['relevance_score']:.2%}"
                    ):
                        st.write(f"**Uploaded:** {doc.upload_date.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Category:** {doc.category or 'General'}")
                        st.write(f"**Type:** {doc.file_type} | **Size:** {doc.file_size / 1024:.1f} KB")
                        
                        st.markdown("**Relevant Content:**")
                        st.text(result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"])
                        
                        if st.button(f"Delete", key=f"del_{doc.id}"):
                            if DocumentService.delete_document(db, doc.id):
                                st.success("Document deleted!")
                                st.rerun()
        else:
            # Get all documents
            category = None if category_filter == "All" else category_filter
            documents = DocumentService.get_documents(db, user_id=st.session_state.user_id, category=category, limit=100)
            
            st.markdown(f"**Total Documents:** {len(documents)}")
            
            if documents:
                for doc in documents:
                    with st.expander(
                        f"📄 {doc.original_filename} - {doc.upload_date.strftime('%Y-%m-%d %H:%M')}"
                    ):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Category:** {doc.category or 'General'}")
                            st.write(f"**Type:** {doc.file_type} | **Size:** {doc.file_size / 1024:.1f} KB")
                            st.write(f"**Words:** {doc.word_count or 'N/A'}")
                            
                            if doc.tags:
                                st.write(f"**Tags:** {', '.join(doc.tags)}")
                            
                            # Get entities
                            entities = db.query(KnowledgeEntity).filter(
                                KnowledgeEntity.document_id == doc.id
                            ).all()
                            
                            if entities:
                                st.markdown("**Extracted Entities:**")
                                
                                # Group by type
                                entity_groups = {}
                                for entity in entities:
                                    if entity.entity_type not in entity_groups:
                                        entity_groups[entity.entity_type] = []
                                    entity_groups[entity.entity_type].append(entity.entity_name)
                                
                                for entity_type, names in entity_groups.items():
                                    st.write(f"- **{entity_type.title()}:** {', '.join(set(names)[:5])}")
                        
                        with col2:
                            st.write(f"**Status:** {'✅ Processed' if doc.is_processed else '⏳ Processing'}")
                            
                            if st.button("🗑️ Delete", key=f"delete_{doc.id}"):
                                if DocumentService.delete_document(db, doc.id):
                                    st.success("Document deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document")
            else:
                st.info("No documents found. Upload documents to get started!")
        
        st.markdown("---")
        
        # Document statistics
        st.subheader("📊 Document Statistics")
        
        stats = DocumentService.get_document_stats(db, user_id=st.session_state.user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", stats["total_documents"])
        
        with col2:
            st.metric("Processed", stats["processed_documents"])
        
        with col3:
            st.metric("Total Size", f"{stats['total_size_mb']} MB")
        
        with col4:
            st.metric("Pending", stats["pending_documents"])
        
        # File type breakdown
        if stats["file_type_distribution"]:
            st.markdown("**File Types:**")
            for file_type, count in stats["file_type_distribution"].items():
                st.write(f"- {file_type}: {count} documents")
    
    finally:
        db.close()
