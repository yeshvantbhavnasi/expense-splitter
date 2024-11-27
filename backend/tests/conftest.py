import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set up test environment variables
os.environ["TESTING"] = "1"
os.environ.setdefault("SUPABASE_URL", "http://test-supabase-url")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret")
