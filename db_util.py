import os
import psycopg2

# PostgreSQL connection setup
def get_postgres_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def close_postgres_connection(conn):
    if conn:
        conn.close()
