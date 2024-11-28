from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from supabase import create_client
from config import get_settings

settings = get_settings()

# Create Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Extract PostgreSQL connection string from Supabase URL
def get_postgres_url():
    project_id = settings.SUPABASE_URL.split('//')[1].split('.')[0]
    db_host = f"db.{project_id}.supabase.co"
    db_password = settings.SUPABASE_DB_PASSWORD  # Get from environment variable
    return f"postgresql://postgres.ehsutvuazqnvhytivisq:{db_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Create SQLAlchemy engine
engine = create_engine(get_postgres_url())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_supabase():
    return supabase
