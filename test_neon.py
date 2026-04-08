import os
from dotenv import load_dotenv
from utils.neon_resume_manager import NeonResumeManager

load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

try:
    mgr = NeonResumeManager(db_url)
    stats = mgr.get_stats()
    print("✅ Connected to Neon Database")
    print(f"   Total Resumes: {stats.get('total_resumes', 0)}")
    print(f"   Total Users: {stats.get('total_users', 0)}")
    print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
except Exception as e:
    print(f"❌ Error: {e}")
