"""Document management service"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import shutil
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Document, DocumentChunk, KnowledgeEntity
from utils.file_processor import FileProcessor, chunk_text
from utils.embedding_manager import embedding_manager
from utils.ai_analyzer import ai_analyzer
import config


class DocumentService:
    """Service for managing documents"""
    
    @staticmethod
    def upload_document(
        db: Session,
        file_path: str,
        original_filename: str,
        user_id: int,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        progress_callback = None
    ) -> Document:
        """Upload and process a document"""
        
        file_path_obj = Path(file_path)
        
        # Create document record
        document = Document(
            filename=file_path_obj.name,
            original_filename=original_filename,
            file_type=file_path_obj.suffix.lower(),
            file_size=file_path_obj.stat().st_size,
            file_path=str(file_path),
            uploaded_by=user_id,
            category=category,
            tags=tags or [],
            is_processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously (in production, use Celery or similar)
        try:
            DocumentService.process_document(db, document.id, progress_callback)
        except Exception as e:
            print(f"Error processing document {document.id}: {str(e)}")
            document.is_processed = False
            db.commit()
        
        return document
    
    @staticmethod
    def process_document(db: Session, document_id: int, progress_callback = None):
        """Process document: extract text, create chunks, generate embeddings, extract entities"""
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if progress_callback:
            progress_callback(10, "Extracting text from document...")
            
        # Extract text from file
        text, word_count, metadata = FileProcessor.process_file(document.file_path)
        
        # Update document
        document.word_count = word_count
        document.title = metadata.get("title", document.original_filename)
        
        if progress_callback:
            progress_callback(30, "Splitting text into semantic chunks...")
            
        # Create text chunks
        chunks = chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        
        # Prepare chunk metadata for FAISS
        chunk_metadata_list = []
        for idx, chunk_content in enumerate(chunks):
            chunk_metadata_list.append({
                "document_id": document.id,
                "chunk_index": idx,
                "filename": document.original_filename,
                "content": chunk_content,
                "user_id": document.uploaded_by
            })
        
        if progress_callback:
            progress_callback(50, "Generating vector embeddings...")
            
        # Add to FAISS index
        embedding_ids = embedding_manager.add_documents(chunks, chunk_metadata_list)
        
        # Create chunk records in database
        for idx, (chunk_content, embedding_id) in enumerate(zip(chunks, embedding_ids)):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk_content,
                embedding_id=str(embedding_id)
            )
            db.add(chunk)
        
        if progress_callback:
            progress_callback(75, "Extracting knowledge entities via AI...")
            
        # Extract entities using AI
        entities = ai_analyzer.extract_entities(text[:6000])  # Use first 6000 chars
        
        if progress_callback:
            progress_callback(90, "Indexing relationships to database...")
            
        # Store entities
        for entity_type, entity_names in entities.items():
            for entity_name in entity_names:
                # Check if entity already exists for this document
                existing = db.query(KnowledgeEntity).filter(
                    KnowledgeEntity.document_id == document.id,
                    KnowledgeEntity.entity_type == entity_type,
                    KnowledgeEntity.entity_name == entity_name
                ).first()
                
                if existing:
                    existing.mention_count += 1
                else:
                    entity = KnowledgeEntity(
                        document_id=document.id,
                        entity_type=entity_type,
                        entity_name=entity_name,
                        mention_count=1
                    )
                    db.add(entity)
        
        # Mark as processed
        document.is_processed = True
        document.processed_at = datetime.utcnow()
        
        db.commit()
        if progress_callback:
            progress_callback(100, "Successfully completed!")
    
    @staticmethod
    def get_documents(
        db: Session,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Document]:
        """Get documents with optional filters"""
        query = db.query(Document)
        
        if user_id:
            query = query.filter(Document.uploaded_by == user_id)
        
        if category:
            query = query.filter(Document.category == category)
        
        query = query.order_by(Document.upload_date.desc()).limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_document(db: Session, document_id: int) -> Optional[Document]:
        """Get single document by ID"""
        return db.query(Document).filter(Document.id == document_id).first()
    
    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        """Delete document and associated data"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Delete file from disk
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
        
        # Remove from FAISS (mark as deleted)
        embedding_manager.delete_document(document_id)
        
        # Delete from database (cascade will delete chunks and entities)
        db.delete(document)
        db.commit()
        
        return True
    
    @staticmethod
    def search_documents(query: str, user_id: int, db: Session, top_k: int = 10) -> List[dict]:
        """Search documents using semantic search, isolated by user_id"""
        results = embedding_manager.search(query, top_k)
        
        # Filter out deleted documents and ensure they belong to this user
        filtered_results = []
        for metadata, distance in results:
            if not metadata.get('deleted', False):
                doc_id = metadata.get("document_id")
                # Direct check against database to ensure absolute user isolation
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc and doc.uploaded_by == user_id:
                    filtered_results.append({
                        "document_id": doc_id,
                        "filename": metadata.get("filename"),
                        "content": metadata.get("content"),
                        "relevance_score": 1.0 / (1.0 + distance)
                    })
        
        return filtered_results
    
    @staticmethod
    def get_document_stats(db: Session, user_id: Optional[int] = None) -> dict:
        """Get document statistics, optionally isolated by user_id"""
        query_total = db.query(Document)
        query_processed = db.query(Document).filter(Document.is_processed == True)
        query_size = db.query(Document).with_entities(func.sum(Document.file_size))
        query_types = db.query(Document.file_type, func.count(Document.id))
        
        if user_id is not None:
            query_total = query_total.filter(Document.uploaded_by == user_id)
            query_processed = query_processed.filter(Document.uploaded_by == user_id)
            query_size = query_size.filter(Document.uploaded_by == user_id)
            query_types = query_types.filter(Document.uploaded_by == user_id)
            
        total_docs = query_total.count()
        processed_docs = query_processed.count()
        total_size = query_size.scalar() or 0
        
        file_types = query_types.group_by(Document.file_type).all()
        
        return {
            "total_documents": total_docs,
            "processed_documents": processed_docs,
            "pending_documents": total_docs - processed_docs,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_type_distribution": {ft: count for ft, count in file_types}
        }
