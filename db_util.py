#import os
import psycopg2

# PostgreSQL connection setup
"""def start_postgres_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)"""
# PostgreSQL connection setup
def start_postgres_connection():
    return psycopg2.connect(database="postgres", user="postgres", password="1234", host="20.174.9.78", port="5432")

def close_postgres_connection(conn):
    if conn:
        conn.close()
