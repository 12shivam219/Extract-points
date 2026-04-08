"""
Security Utilities - Input validation, sanitization, and error handling
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize and validate user inputs to prevent security issues"""
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE_RESUME = 10 * 1024 * 1024  # 10 MB for DOCX
    MAX_FILE_SIZE_TEXT = 5 * 1024 * 1024     # 5 MB for text
    MAX_FILENAME_LENGTH = 255
    
    # Dangerous characters in filenames
    DANGEROUS_CHARS = r'[<>:"|?*\x00]'
    
    @staticmethod
    def validate_filename(filename: str, max_length: int = 255) -> Tuple[bool, str]:
        """
        Validate filename to prevent path traversal and injection attacks.
        
        Args:
            filename: Filename to validate
            max_length: Maximum allowed filename length
            
        Returns:
            (is_valid, sanitized_filename_or_error_message)
        """
        if not filename or not filename.strip():
            return False, "Filename cannot be empty"
        
        # Check length
        if len(filename) > max_length:
            return False, f"Filename too long (max {max_length} characters)"
        
        # Remove dangerous characters
        sanitized = re.sub(InputSanitizer.DANGEROUS_CHARS, '', filename)
        
        # Remove path traversal attempts
        sanitized = sanitized.replace('..', '').replace('//', '')
        
        # Prevent directory traversal
        if '/' in sanitized or '\\' in sanitized or sanitized.startswith('.'):
            return False, "Filename contains invalid path characters"
        
        if not sanitized:
            return False, "Filename contains only invalid characters"
        
        return True, sanitized
    
    @staticmethod
    def validate_file_size(file_size: int, file_type: str = 'text') -> Tuple[bool, str]:
        """
        Validate file size based on type.
        
        Args:
            file_size: File size in bytes
            file_type: 'resume' or 'text'
            
        Returns:
            (is_valid, error_message)
        """
        max_size = InputSanitizer.MAX_FILE_SIZE_RESUME if file_type == 'resume' else InputSanitizer.MAX_FILE_SIZE_TEXT
        
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum: {max_mb:.1f} MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_base: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate file path to prevent path traversal attacks.
        
        Args:
            file_path: Path to validate
            allowed_base: Optional base directory to ensure file is within
            
        Returns:
            (is_valid, error_message_or_normalized_path)
        """
        try:
            # Normalize the path
            normalized = Path(file_path).resolve()
            
            # Check for path traversal attempts
            if '..' in str(file_path):
                return False, "Path traversal detected"
            
            # If allowed_base is specified, ensure file is within it
            if allowed_base:
                allowed_base_resolved = Path(allowed_base).resolve()
                try:
                    # This will raise ValueError if normalized is not relative to allowed_base
                    normalized.relative_to(allowed_base_resolved)
                except ValueError:
                    return False, f"File must be within {allowed_base}"
            
            return True, str(normalized)
        
        except Exception as e:
            logger.warning(f"Invalid file path: {str(e)}")
            return False, "Invalid file path"
    
    @staticmethod
    def sanitize_error_message(error: Exception, user_facing: bool = True) -> str:
        """
        Sanitize error messages to prevent information disclosure.
        
        Args:
            error: Exception object
            user_facing: If True, return generic message; if False, return detailed
            
        Returns:
            Sanitized error message
        """
        error_str = str(error)
        
        # Don't expose sensitive information to users
        if user_facing:
            # Check for common sensitive patterns
            sensitive_patterns = [
                r'password',
                r'api[_-]?key',
                r'token',
                r'secret',
                r'database[_-]?url',
                r'credentials',
                r'/Users/',
                r'C:\\',
                r'@',  # Email/credentials
            ]
            
            # If error contains sensitive info, return generic message
            for pattern in sensitive_patterns:
                if re.search(pattern, error_str, re.IGNORECASE):
                    # Log the actual error for debugging but don't show to user
                    logger.error(f"Detailed error: {error_str}")
                    return "An error occurred. Please check your input and try again."
        
        # For non-sensitive errors, return as-is
        return error_str


class SecurityHeader:
    """Generate secure HTTP headers for Streamlit"""
    
    @staticmethod
    def get_secure_headers() -> dict:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        }


class FileUploadValidator:
    """Centralized file upload validation"""
    
    ALLOWED_RESUME_TYPES = {'.docx'}
    ALLOWED_TEXT_TYPES = {'.txt'}
    
    @staticmethod
    def validate_resume_upload(file_obj, filename: str) -> Tuple[bool, str]:
        """
        Validate resume file upload.
        
        Returns:
            (is_valid, error_message)
        """
        # Validate filename
        is_valid, msg = InputSanitizer.validate_filename(filename)
        if not is_valid:
            return False, f"Invalid filename: {msg}"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in FileUploadValidator.ALLOWED_RESUME_TYPES:
            return False, "Only .docx files allowed for resumes"
        
        # Check file size
        if hasattr(file_obj, 'size'):
            file_size = file_obj.size
        else:
            # If size not available, read and check
            content = file_obj.read()
            file_obj.seek(0)
            file_size = len(content)
        
        is_valid, msg = InputSanitizer.validate_file_size(file_size, file_type='resume')
        if not is_valid:
            return False, msg
        
        return True, ""
    
    @staticmethod
    def validate_text_upload(file_obj, filename: str) -> Tuple[bool, str]:
        """
        Validate text file upload.
        
        Returns:
            (is_valid, error_message)
        """
        # Validate filename
        is_valid, msg = InputSanitizer.validate_filename(filename)
        if not is_valid:
            return False, f"Invalid filename: {msg}"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in FileUploadValidator.ALLOWED_TEXT_TYPES:
            return False, "Only .txt files allowed for text"
        
        # Check file size
        if hasattr(file_obj, 'size'):
            file_size = file_obj.size
        else:
            content = file_obj.read()
            file_obj.seek(0)
            file_size = len(content)
        
        is_valid, msg = InputSanitizer.validate_file_size(file_size, file_type='text')
        if not is_valid:
            return False, msg
        
        return True, ""


class SecureLogger:
    """Logger that prevents secret exposure"""
    
    SENSITIVE_PATTERNS = {
        'api_key': r'[a-zA-Z0-9_]{20,}',
        'password': r'password["\']?\s*[:=]\s*["\']?[^"\']{6,}',
        'token': r'token["\']?\s*[:=]\s*["\']?[^"\']{20,}',
        'database_url': r'(postgresql|mysql|mongodb)://[^/]+:[^@]+@',
    }
    
    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Remove sensitive information from log messages"""
        for key, pattern in SecureLogger.SENSITIVE_PATTERNS.items():
            message = re.sub(pattern, f'[REDACTED_{key.upper()}]', message, flags=re.IGNORECASE)
        return message
    
    @staticmethod
    def safe_log(logger_obj, level: str, message: str):
        """Safely log messages without exposing secrets"""
        sanitized = SecureLogger.sanitize_log_message(message)
        getattr(logger_obj, level)(sanitized)
