"""Database connection and session management"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import config
from database.models import Base


# Create engine with SQLite optimizations
def create_db_engine():
    """Create database engine with proper configuration"""
    engine = create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Enable WAL mode for better concurrency
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
    
    return engine


# Create engine
engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    try:
        # Ensure data directory exists
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print(f"✅ Database initialized at: {db_path}")
    except Exception as e:
        print(f"⚠️ Database initialization error: {str(e)}")
        raise


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def backup_database(backup_path: str = None):
    """Create database backup"""
    import shutil
    from datetime import datetime
    from pathlib import Path
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config.BACKUP_DIR / f"backup_{timestamp}.db"
    
    # Get database file path
    db_path = config.DATABASE_URL.replace("sqlite:///", "")
    db_path = Path(db_path)
    
    # Check if database file exists
    if not db_path.exists():
        print(f"⚠️ Database file not found: {db_path}")
        return None
    
    # Ensure backup directory exists
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return None


def restore_database(backup_path: str):
    """Restore database from backup"""
    import shutil
    from pathlib import Path
    
    # Get database file path
    db_path = config.DATABASE_URL.replace("sqlite:///", "")
    db_path = Path(db_path)
    
    # Close all connections
    engine.dispose()
    
    try:
        # Restore backup
        shutil.copy2(backup_path, db_path)
        print(f"✅ Database restored from: {backup_path}")
    except Exception as e:
        print(f"❌ Restore failed: {str(e)}")
        raise


def optimize_database():
    """Run database optimization"""
    with get_db_context() as db:
        db.execute("VACUUM")
        db.execute("ANALYZE")
    print("✅ Database optimized")
