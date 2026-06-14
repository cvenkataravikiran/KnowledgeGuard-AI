"""Complete application setup script"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Run complete setup"""
    print("=" * 60)
    print("KnowledgeGuard AI - Automated Setup")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Install all required Python packages")
    print("  2. Verify system requirements")
    print("  3. Initialize database (if needed)")
    print()
    
    response = input("Continue with setup? (y/n): ")
    if response.lower() != 'y':
        print("Setup cancelled.")
        return
    
    # Step 1: Install dependencies
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python packages"
    ):
        print("\n⚠️  Package installation failed. Please install manually:")
        print("   pip install -r requirements.txt")
        return
    
    # Step 2: Check system
    if not run_command(
        f"{sys.executable} check_system.py",
        "Verifying system requirements"
    ):
        print("\n⚠️  System check found issues.")
        print("   Review the output above and fix any problems.")
        return
    
    # Step 3: Check if database needs migration
    db_path = Path('knowledgeguard.db')
    if db_path.exists():
        print("\n" + "=" * 60)
        print("📊 Existing database detected")
        print("=" * 60)
        response = input("\nDo you need to fix the database schema? (y/n): ")
        if response.lower() == 'y':
            if not run_command(
                f"{sys.executable} fix_database.py",
                "Fixing database schema"
            ):
                print("\n⚠️  Database fix failed.")
                return
    
    # Setup complete
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("To start the application:")
    print(f"  streamlit run app.py")
    print()
    print("Default login:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("Next steps:")
    print("  1. Start the application")
    print("  2. Login with the default credentials")
    print("  3. Upload your documents in the Upload Center")
    print("  4. Explore features like Risk Analysis and Knowledge Graph")
    print()


if __name__ == "__main__":
    main()
