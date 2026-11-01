import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
from contextlib import contextmanager

@contextmanager
def get_db_cursor():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database=os.getenv('POSTGRES_DB', 'Vector_test'),
            user=os.getenv('POSTGRES_USER', 'Vector_Test'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        conn.autocommit = True
        cur = conn.cursor()
        yield cur
    except Exception as e:
        print(f"❌ DB error: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()