"""
Neon Resume Manager - Handle resume upload and storage in Neon PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pathlib import Path
from typing import List, Dict, Tuple
from io import BytesIO
import tempfile
from datetime import datetime
from functools import lru_cache

from utils.bookmark_manager import BookmarkManager
from utils.text_processor import TextProcessor


class NeonResumeManager:
    """Manage resume uploads and storage in Neon database"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.bookmark_manager = BookmarkManager()
        self.local_storage = Path("./resumes_uploaded")
        self.local_storage.mkdir(parents=True, exist_ok=True)
        self._connection = None
    
    def get_connection(self):
        """Get or create persistent connection"""
        try:
            if not self._connection or self._connection.closed:
                self._connection = psycopg2.connect(self.db_url)
            return self._connection
        except:
            self._connection = psycopg2.connect(self.db_url)
            return self._connection
    
    def upload_resume(self, file_content: BytesIO, filename: str, user_email: str = None) -> Tuple[bool, str]:
        """Upload resume and store metadata in Neon"""
        try:
            # Step 1: Extract technologies from filename
            techs = self._extract_techs_from_filename(filename)
            
            # Step 2: Save file locally/temp
            file_path = self.local_storage / filename
            with open(file_path, 'wb') as f:
                f.write(file_content.getvalue())
            
            # Step 3: Extract bookmarks
            bookmarks = self.bookmark_manager.detect_bookmarks(str(file_path))
            
            # Step 4: Get file size
            file_size = file_path.stat().st_size
            
            # Step 5: Store in Neon database
            user_id = self._get_or_create_user(user_email) if user_email else None
            
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO resumes 
                (user_id, filename, s3_path, technologies, bookmarks, size, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (user_id, filename, str(file_path), techs, bookmarks, file_size))
            
            resume_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            return True, f"Resume stored! ID: {resume_id}"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_user_resumes(self, user_email: str) -> Tuple[bool, List[Dict]]:
        """Get all resumes for a user from Neon"""
        try:
            user_id = self._get_user_id(user_email)
            if not user_id:
                return True, []
            
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Optimized query - limit results
            cur.execute("""
                SELECT id, filename, technologies, bookmarks, size, created_at
                FROM resumes
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            resumes = cur.fetchall()
            cur.close()
            
            return True, list(resumes) if resumes else []
        
        except Exception as e:
            return False, []
    
    def get_all_public_resumes(self) -> Tuple[bool, List[Dict]]:
        """Get all resumes from database (for admin/search)"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT id, filename, technologies, bookmarks, size, created_at
                FROM resumes
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT 100
            """)
            
            resumes = cur.fetchall()
            cur.close()
            
            return True, list(resumes) if resumes else []
        
        except Exception as e:
            return False, []
    
    def search_resumes_by_tech(self, technology: str) -> Tuple[bool, List[Dict]]:
        """Search resumes by technology"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT id, filename, technologies, bookmarks, size, created_at
                FROM resumes
                WHERE deleted_at IS NULL 
                AND technologies @> ARRAY[%s]
                ORDER BY created_at DESC
                LIMIT 50
            """, (technology,))
            
            resumes = cur.fetchall()
            cur.close()
            
            return True, list(resumes) if resumes else []
        
        except Exception as e:
            return False, []
    
    def delete_resume(self, resume_id: int, user_email: str) -> Tuple[bool, str]:
        """Soft delete resume (mark as deleted)"""
        try:
            user_id = self._get_user_id(user_email)
            
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Check if user owns this resume
            cur.execute("""
                SELECT id FROM resumes 
                WHERE id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            if not cur.fetchone():
                cur.close()
                return False, "Resume not found or permission denied"
            
            # Soft delete
            cur.execute("""
                UPDATE resumes 
                SET deleted_at = NOW()
                WHERE id = %s
            """, (resume_id,))
            
            conn.commit()
            cur.close()
            
            return True, "Resume deleted"
        
        except Exception as e:
            return False, str(e)
    
    def get_resume_file(self, resume_id: int) -> Tuple[bool, BytesIO]:
        """Get resume file content"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s3_path FROM resumes WHERE id = %s
            """, (resume_id,))
            
            result = cur.fetchone()
            cur.close()
            
            if not result:
                return False, None
            
            file_path = result[0]
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = BytesIO(f.read())
                return True, content
            
            return False, None
        
        except Exception as e:
            return False, None
    
    def _extract_techs_from_filename(self, filename: str) -> List[str]:
        """Extract technology names from filename"""
        # Format: PersonName_Tech1_Tech2_Tech3.docx
        name_without_ext = filename.replace('.docx', '').replace('.DOCX', '')
        parts = name_without_ext.split('_')
        
        if len(parts) > 1:
            # Skip first part (name), rest are technologies
            return parts[1:]
        
        return []
    
    def _get_or_create_user(self, email: str) -> int:
        """Get user ID or create new user"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Try to get existing user
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            
            if result:
                user_id = result[0]
            else:
                # Create new user
                cur.execute("""
                    INSERT INTO users (email, created_at)
                    VALUES (%s, NOW())
                    RETURNING id
                """, (email,))
                user_id = cur.fetchone()[0]
                conn.commit()
            
            cur.close()
            return user_id
        
        except Exception as e:
            return None
    
    def _get_user_id(self, email: str) -> int:
        """Get user ID by email"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email,))
            result = cur.fetchone()
            
            cur.close()
            
            return result[0] if result else None
        
        except Exception as e:
            return None
    
    def get_stats(self) -> Dict:
        """Get database statistics (cached at session level)"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Batch query in single round trip
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM resumes WHERE deleted_at IS NULL) as total_resumes,
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM job_applications) as total_jobs
            """)
            
            row = cur.fetchone()
            cur.close()
            
            return {
                "total_resumes": row[0] if row else 0,
                "total_users": row[1] if row else 0,
                "total_jobs": row[2] if row else 0
            }
        
        except Exception as e:
            return {"total_resumes": 0, "total_users": 0, "total_jobs": 0}
