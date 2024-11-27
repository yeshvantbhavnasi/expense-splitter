from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from database import SQLALCHEMY_DATABASE_URL
import models
from database import Base

def init_db():
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Created database: {engine.url}")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Created all database tables")

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed")
