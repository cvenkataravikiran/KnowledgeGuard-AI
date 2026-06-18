"""KnowledgeGuard AI - Main Application"""
import streamlit as st
from database.database import init_db, backup_database
from database.models import User
from utils.security import verify_password
from database.database import get_db
import config

# Page configuration
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
try:
    init_db()
except Exception as e:
    st.error(f"❌ Database initialization failed: {str(e)}")
    st.stop()

# Check if API key is configured
if not config.GROQ_API_KEY:
    st.warning("⚠️ GROQ_API_KEY not configured. AI features will be limited. Please add it in Streamlit secrets (Settings → Secrets) or .env file.")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None


def create_default_user():
    """Create default admin user if none exists"""
    db = get_db()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            from utils.security import hash_password
            from datetime import datetime
            
            admin_user = User(
                username="admin",
                email="admin@knowledgeguard.ai",
                hashed_password=hash_password("admin123"),
                full_name="System Administrator",
                role="admin",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")
    finally:
        db.close()


def login_page():
    """Login page"""
    st.title("🛡️ KnowledgeGuard AI")
    st.subheader("AI-Powered Knowledge Loss Detection Platform")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.subheader("Login")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_login, col_register = st.columns(2)
        
        with col_login:
            if st.button("Login", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    db = get_db()
                    try:
                        user = db.query(User).filter(User.username == username).first()
                        
                        if user and verify_password(password, user.hashed_password):
                            if user.is_active:
                                st.session_state.authenticated = True
                                st.session_state.user_id = user.id
                                st.session_state.username = user.username
                                st.session_state.user_role = user.role
                                
                                # Update last login
                                from datetime import datetime
                                user.last_login = datetime.utcnow()
                                db.commit()
                                
                                st.success(f"Welcome back, {user.full_name or user.username}!")
                                st.rerun()
                            else:
                                st.error("Account is inactive. Contact administrator.")
                        else:
                            st.error("Invalid username or password")
                    finally:
                        db.close()
        
        with col_register:
            if st.button("Register", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        



def register_page():
    """Registration page"""
    st.title("Create Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if not all([username, email, password, confirm_password]):
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    db = get_db()
                    try:
                        # Check if username exists
                        existing_user = db.query(User).filter(
                            (User.username == username) | (User.email == email)
                        ).first()
                        
                        if existing_user:
                            st.error("Username or email already exists")
                        else:
                            from utils.security import hash_password
                            from datetime import datetime
                            
                            new_user = User(
                                username=username,
                                email=email,
                                hashed_password=hash_password(password),
                                full_name=full_name,
                                role="user",
                                is_active=True,
                                created_at=datetime.utcnow()
                            )
                            db.add(new_user)
                            db.commit()
                            
                            st.success("Account created successfully! Please login.")
                            st.session_state.show_register = False
                            st.rerun()
                    finally:
                        db.close()
        
        if st.button("Back to Login"):
            st.session_state.show_register = False
            st.rerun()


def main_app():
    """Main application after login"""
    # Sidebar
    with st.sidebar:
        st.title("🛡️ KnowledgeGuard AI")
        st.write(f"Welcome, **{st.session_state.username}**")
        st.write(f"Role: **{st.session_state.user_role}**")
        st.markdown("---")
        
        # Navigation
        pages = {
            "🏠 Home": "pages/home.py",
            "📤 Upload Center": "pages/upload_center.py",
            "📚 Documents": "pages/documents.py",
            "🌐 Knowledge Graph": "pages/knowledge_graph.py",
            "⚠️ Risk Analysis": "pages/risk_analysis.py",
            "🚨 Exit Simulator": "pages/exit_simulator.py",
            "💬 AI Assistant": "pages/ai_assistant.py",
            "⚙️ Settings": "pages/settings.py"
        }
        
        if st.session_state.user_role == "admin":
            pages["👑 Admin"] = "pages/admin.py"
        
        page = st.radio("Navigation", list(pages.keys()))
        
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()
    
    # Load selected page
    if page == "🏠 Home":
        from pages import home
        home.show()
    elif page == "📤 Upload Center":
        from pages import upload_center
        upload_center.show()
    elif page == "📚 Documents":
        from pages import documents
        documents.show()
    elif page == "🌐 Knowledge Graph":
        from pages import knowledge_graph
        knowledge_graph.show()
    elif page == "⚠️ Risk Analysis":
        from pages import risk_analysis
        risk_analysis.show()
    elif page == "🚨 Exit Simulator":
        from pages import exit_simulator
        exit_simulator.show()
    elif page == "💬 AI Assistant":
        from pages import ai_assistant
        ai_assistant.show()
    elif page == "⚙️ Settings":
        from pages import settings
        settings.show()
    elif page == "👑 Admin":
        from pages import admin
        admin.show()


# Main execution
if __name__ == "__main__":
    # Create default user
    create_default_user()
    
    # Show appropriate page
    if st.session_state.authenticated:
        main_app()
    else:
        if st.session_state.get('show_register', False):
            register_page()
        else:
            login_page()
