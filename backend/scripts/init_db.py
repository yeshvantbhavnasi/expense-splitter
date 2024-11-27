import sys
import os

# Add parent directory to path to import from parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
import models

def init_db():
    print("Creating database tables...")
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
