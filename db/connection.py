import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    Create and return a database connection
    """
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise
