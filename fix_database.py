"""Simple database reset script - fixes user isolation"""
import shutil
from pathlib import Path
from datetime import datetime
from database.models import Base, User
from database.database import engine, SessionLocal
from utils.security import hash_password


def main():
    print("🔧 Fixing database schema...")
    
    # Backup existing database
    db_path = Path("knowledgeguard.db")
    if db_path.exists():
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        print(f"📦 Backup: {backup_path}")
        
        # Preserve users
        try:
            db = SessionLocal()
            users = db.query(User).all()
            user_data = [(u.username, u.email, u.hashed_password, u.full_name, u.role, u.is_active) for u in users]
            db.close()
            print(f"💾 Preserved {len(user_data)} users")
        except:
            user_data = []
    else:
        user_data = []
    
    # Recreate database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Schema updated")
    
    # Restore users
    if user_data:
        db = SessionLocal()
        for username, email, pwd, name, role, active in user_data:
            user = User(username=username, email=email, hashed_password=pwd, 
                       full_name=name, role=role, is_active=active, created_at=datetime.utcnow())
            db.add(user)
        db.commit()
        db.close()
        print(f"✅ Restored {len(user_data)} users")
    else:
        # Create default admin
        db = SessionLocal()
        admin = User(username="admin", email="admin@knowledgeguard.ai",
                    hashed_password=hash_password("admin123"), full_name="Administrator",
                    role="admin", is_active=True, created_at=datetime.utcnow())
        db.add(admin)
        db.commit()
        db.close()
        print("✅ Created admin user")
    
    # Clear FAISS
    faiss_dir = Path("faiss_index")
    if faiss_dir.exists():
        for file in faiss_dir.glob("*"):
            if file.is_file():
                file.unlink()
        print("✅ Cleared vector index")
    
    print("\n✨ Done! Re-upload documents to rebuild data.")


if __name__ == "__main__":
    main()
