"""AI Chat Assistant Page"""
import streamlit as st
from datetime import datetime
from database.database import get_db
from database.models import ChatHistory
from services.document_service import DocumentService
from utils.ai_analyzer import ai_analyzer


def show():
    st.title("💬 AI Knowledge Assistant")
    st.markdown("Ask questions about your organizational knowledge")
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for source in message["sources"]:
                        st.write(f"- {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your organization..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Search for relevant documents
                db = get_db()
                try:
                    search_results = DocumentService.search_documents(prompt, user_id=st.session_state.user_id, db=db, top_k=5)
                    
                    if not search_results:
                        response = "I couldn't find any relevant documents to answer your question. Please upload more documents or try rephrasing your question."
                        sources = []
                    else:
                        # Extract context from search results
                        context_docs = [result["content"] for result in search_results]
                        
                        # Get AI answer
                        ai_response = ai_analyzer.answer_question(prompt, context_docs)
                        
                        response = ai_response["answer"]
                        sources = [result["filename"] for result in search_results]
                    
                    # Display response
                    st.markdown(response)
                    
                    if sources:
                        with st.expander("📚 Sources Used"):
                            for source in sources:
                                st.write(f"- {source}")
                    
                    # Add to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
                    
                    # Save to database
                    chat_record = ChatHistory(
                        user_id=st.session_state.user_id,
                        user_message=prompt,
                        ai_response=response,
                        source_documents=[r["document_id"] for r in search_results] if search_results else [],
                        confidence_score=ai_response.get("confidence", 0.0) if search_results else 0.0
                    )
                    db.add(chat_record)
                    db.commit()
                finally:
                    db.close()
    
    # Sidebar with suggestions and history
    with st.sidebar:
        st.markdown("### 💡 Example Questions")
        
        examples = [
            "Who owns the deployment knowledge?",
            "Which employee is most critical?",
            "What systems depend on [employee name]?",
            "What documentation is missing?",
            "List all projects and their owners",
            "What are the high-risk systems?",
            "Show me all SOPs we have",
            "Who handles the payment gateway?"
        ]
        
        for example in examples:
            if st.button(example, key=f"ex_{example}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": example})
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        
        # Recent conversations
        st.markdown("### 📜 Recent Conversations")
        
        db = get_db()
        try:
            recent_chats = db.query(ChatHistory).filter(
                ChatHistory.user_id == st.session_state.user_id
            ).order_by(
                ChatHistory.created_at.desc()
            ).limit(5).all()
            
            if recent_chats:
                for chat in recent_chats:
                    with st.expander(
                        chat.user_message[:50] + "..." if len(chat.user_message) > 50 else chat.user_message
                    ):
                        st.write(f"**Q:** {chat.user_message}")
                        st.write(f"**A:** {chat.ai_response[:200]}...")
                        st.write(f"*{chat.created_at.strftime('%Y-%m-%d %H:%M')}*")
            else:
                st.info("No chat history yet")
        
        finally:
            db.close()
    
    # Help section
    st.markdown("---")
    
    with st.expander("ℹ️ How to Use the AI Assistant"):
        st.markdown("""
        ### Tips for Better Answers
        
        1. **Be Specific**: Instead of "Tell me about systems", ask "Which systems does John own?"
        
        2. **Ask About People**: 
           - "Who is responsible for the API gateway?"
           - "What projects is Sarah working on?"
        
        3. **Ask About Systems**:
           - "List all critical systems"
           - "What documentation exists for the payment system?"
        
        4. **Ask About Risks**:
           - "Which employees are high risk?"
           - "What happens if David leaves?"
        
        5. **Ask About Documentation**:
           - "What SOPs are missing?"
           - "Show me documentation gaps"
        
        ### How It Works
        
        The AI assistant uses **RAG (Retrieval Augmented Generation)**:
        
        1. Your question is converted to a semantic search query
        2. Relevant documents are retrieved from the vector database
        3. The AI generates an answer based on the retrieved context
        4. Sources are cited so you can verify the information
        
        ### Limitations
        
        - Answers are based only on uploaded documents
        - The AI cannot access information not present in your knowledge base
        - For best results, ensure your documents are comprehensive and up-to-date
        """)
