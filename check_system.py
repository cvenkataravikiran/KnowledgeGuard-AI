"""System readiness check script"""
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit', 'sqlalchemy', 'pandas', 'numpy', 'faiss-cpu',
        'sentence-transformers', 'groq', 'python-dotenv', 'bcrypt',
        'python-jose', 'PyMuPDF', 'python-docx', 'openpyxl', 'plotly', 'pyvis'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages installed")
    return True


def check_directories():
    """Check if required directories exist"""
    dirs = ['uploads', 'backups', 'faiss_index', 'logs']
    
    for d in dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {d}")
        else:
            print(f"✅ Directory exists: {d}")
    
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Copy .env.example to .env and configure it")
        return False
    
    print("✅ .env file found")
    
    # Check for required variables
    required_vars = ['GROQ_API_KEY', 'SECRET_KEY']
    with open(env_path) as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content or f'{var}=' not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Required environment variables configured")
    return True


def check_database():
    """Check database status"""
    db_path = Path('knowledgeguard.db')
    
    if not db_path.exists():
        print("ℹ️  Database doesn't exist yet (will be created on first run)")
        return True
    
    print(f"✅ Database exists ({db_path.stat().st_size / 1024:.1f} KB)")
    
    # Check if schema needs migration
    try:
        from database.database import engine
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'employees' in tables:
            # Check if user_id column exists
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(employees)"))
                columns = [row[1] for row in result]
                
                if 'user_id' not in columns:
                    print("⚠️  Database schema needs migration")
                    print("   Run: python fix_database.py")
                    return False
        
        print("✅ Database schema is up to date")
        return True
    
    except Exception as e:
        print(f"⚠️  Could not check database: {e}")
        return True  # Don't fail, let app handle it


def main():
    """Run all checks"""
    print("=" * 60)
    print("KnowledgeGuard AI - System Readiness Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Environment File", check_env_file),
        ("Database", check_database),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        print("-" * 40)
        if not check_func():
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed! System is ready.")
        print()
        print("To start the application:")
        print("  streamlit run app.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
