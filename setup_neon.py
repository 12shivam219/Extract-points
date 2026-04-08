#!/usr/bin/env python3
"""
Setup Neon PostgreSQL database for resume storage
Run once: python setup_neon.py
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    print("Get free Neon database: https://neon.tech")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Create resumes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            filename VARCHAR(255) NOT NULL,
            s3_path VARCHAR(500),
            technologies TEXT[],
            bookmarks TEXT[],
            size INT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deleted_at TIMESTAMP
        )
    """)
    
    # Create resume_versions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resume_versions (
            id SERIAL PRIMARY KEY,
            resume_id INT REFERENCES resumes(id) ON DELETE CASCADE,
            version_number INT,
            s3_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Create job_applications table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            resume_id INT REFERENCES resumes(id),
            job_title VARCHAR(255),
            company_name VARCHAR(255),
            job_description TEXT,
            generated_points TEXT,
            recruiter_email VARCHAR(255),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Create indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
        CREATE INDEX IF NOT EXISTS idx_resumes_filename ON resumes(filename);
        CREATE INDEX IF NOT EXISTS idx_job_apps_user_id ON job_applications(user_id);
        CREATE INDEX IF NOT EXISTS idx_job_apps_created ON job_applications(created_at);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Neon database setup complete!")
    print("✅ Tables created: users, resumes, resume_versions, job_applications")
    print("\nYour database is ready to use!")
    print("DATABASE_URL:", DATABASE_URL.split("@")[1][:50] + "...")
    
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
