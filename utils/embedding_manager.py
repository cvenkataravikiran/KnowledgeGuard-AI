"""FAISS vector database management for semantic search"""
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional
import config


class EmbeddingManager:
    """Manage embeddings and FAISS index for semantic search"""
    
    def __init__(self):
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.dimension = config.EMBEDDING_DIMENSION
        self.index_path = config.FAISS_INDEX_DIR / "document_index.faiss"
        self.metadata_path = config.FAISS_INDEX_DIR / "metadata.pkl"
        
        # Initialize or load index
        if self.index_path.exists():
            self.load_index()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype('float32')
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.astype('float32')
    
    def add_documents(self, texts: List[str], metadata: List[dict]) -> List[int]:
        """
        Add documents to FAISS index
        
        Args:
            texts: List of text chunks
            metadata: List of metadata dicts for each chunk
        
        Returns:
            List of assigned IDs
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts)
        
        # Get starting ID
        start_id = len(self.metadata)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        for i, meta in enumerate(metadata):
            meta['id'] = start_id + i
            self.metadata.append(meta)
        
        # Save index
        self.save_index()
        
        return list(range(start_id, start_id + len(texts)))
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[dict, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (metadata, distance) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(dist)))
        
        return results
    
    def delete_document(self, document_id: int):
        """
        Remove document from index (mark metadata as deleted)
        Note: FAISS doesn't support deletion, so we mark metadata
        """
        for meta in self.metadata:
            if meta.get('document_id') == document_id:
                meta['deleted'] = True
        
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load_index(self):
        """Load FAISS index and metadata from disk"""
        self.index = faiss.read_index(str(self.index_path))
        
        if self.metadata_path.exists():
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.metadata = []
    
    def rebuild_index(self, documents_data: List[Tuple[str, dict]]):
        """
        Rebuild entire index from scratch
        
        Args:
            documents_data: List of (text, metadata) tuples
        """
        # Create new index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        
        if not documents_data:
            self.save_index()
            return
        
        # Extract texts and metadata
        texts = [text for text, _ in documents_data]
        metadata_list = [meta for _, meta in documents_data]
        
        # Add documents
        self.add_documents(texts, metadata_list)
    
    def get_index_stats(self) -> dict:
        """Get statistics about the index"""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
            "active_documents": len([m for m in self.metadata if not m.get('deleted', False)])
        }


# Global instance
embedding_manager = EmbeddingManager()
