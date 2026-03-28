#!/usr/bin/env python3
"""
Bookmark Management System
Handles detection, mapping, and profile management for flexible resume injection
"""

import json
import os
from pathlib import Path
from docx import Document
from typing import Dict, List, Tuple
import re


class BookmarkManager:
    """Manages bookmark detection and mapping across different resume templates."""
    
    PROFILES_DIR = Path.home() / ".extract_points" / "bookmark_profiles"
    
    # Pattern keywords for smart matching
    PATTERN_KEYWORDS = {
        'responsibilities': ['responsibilities', 'accountabilities', 'accomplishments', 'highlights'],
        'company': ['company', 'client', 'organization', 'employer'],
        'skills': ['skills', 'technical', 'technologies', 'expertise'],
        'education': ['education', 'education:', 'degree', 'certification'],
    }
    
    def __init__(self):
        """Initialize bookmark manager."""
        self.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    def detect_bookmarks(self, resume_bytes) -> List[str]:
        """
        Auto-detect all bookmarks in a document.
        Returns list of bookmark names in order found.
        """
        try:
            doc = Document(resume_bytes)
            bookmarks = []
            
            for element in doc.element.iter():
                tag = element.tag
                if 'bookmarkStart' in tag:
                    if hasattr(element, 'attrib'):
                        for attr_name, attr_val in element.attrib.items():
                            if 'name' in attr_name.lower():
                                if attr_val not in bookmarks:
                                    bookmarks.append(attr_val)
            
            return sorted(bookmarks)  # Sort for consistency
        except Exception as e:
            print(f"Error detecting bookmarks: {e}")
            return []
    
    def match_pattern(self, bookmark_name: str) -> Tuple[str, float]:
        """
        Pattern match a bookmark name to determine its type.
        Returns: (pattern_type, confidence_score)
        """
        bookmark_lower = bookmark_name.lower()
        best_match = ('unknown', 0.0)
        
        for pattern_type, keywords in self.PATTERN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in bookmark_lower:
                    # Higher confidence for exact substring matches
                    confidence = len(keyword) / len(bookmark_lower)
                    if confidence > best_match[1]:
                        best_match = (pattern_type, confidence)
        
        return best_match
    
    def suggest_mappings(self, bookmarks: List[str], num_cycles: int) -> Dict[int, str]:
        """
        Suggest automatic cycle-to-bookmark mappings.
        
        Strategy:
        1. Try pattern matching (responsibilities → likely company sections)
        2. Fall back to sequential ordering
        3. Prioritize "responsibilities" pattern bookmarks
        """
        if not bookmarks:
            return {}
        
        mapping = {}
        
        # Filter bookmarks that look like responsibility sections
        responsibility_bookmarks = []
        other_bookmarks = []
        
        for bm in bookmarks:
            pattern_type, confidence = self.match_pattern(bm)
            if pattern_type == 'responsibilities' and confidence > 0.2:
                responsibility_bookmarks.append(bm)
            else:
                other_bookmarks.append(bm)
        
        # Use responsibility bookmarks first, then others
        ordered_bookmarks = responsibility_bookmarks + other_bookmarks
        
        # Map cycles sequentially to available bookmarks
        for cycle_num in range(1, num_cycles + 1):
            if cycle_num - 1 < len(ordered_bookmarks):
                mapping[cycle_num] = ordered_bookmarks[cycle_num - 1]
        
        return mapping
    
    def save_profile(self, profile_name: str, bookmarks: List[str], 
                     mapping: Dict[int, str], resume_name: str = "") -> bool:
        """
        Save a bookmark mapping profile for future use.
        
        Args:
            profile_name: Name of the profile (e.g., "Java Resume")
            bookmarks: List of all bookmarks found
            mapping: Cycle → Bookmark mapping
            resume_name: Optional original resume filename
        
        Returns:
            True if saved successfully
        """
        try:
            profile_data = {
                'profile_name': profile_name,
                'resume_name': resume_name,
                'bookmarks': bookmarks,
                'mapping': {str(k): v for k, v in mapping.items()},  # Convert int keys to str for JSON
                'created_at': str(Path.cwd()),
            }
            
            # Sanitize profile name for filename
            filename = re.sub(r'[^\w\s-]', '', profile_name).strip().replace(' ', '_') + '.json'
            filepath = self.PROFILES_DIR / filename
            
            with open(filepath, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            print(f"✓ Profile saved: {profile_name}")
            return True
        except Exception as e:
            print(f"✗ Error saving profile: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Dict:
        """
        Load a saved bookmark profile.
        
        Returns:
            Dict with keys: 'bookmarks', 'mapping', 'resume_name'
            Empty dict if not found
        """
        try:
            filename = re.sub(r'[^\w\s-]', '', profile_name).strip().replace(' ', '_') + '.json'
            filepath = self.PROFILES_DIR / filename
            
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                # Convert string keys back to int for mapping
                data['mapping'] = {int(k): v for k, v in data['mapping'].items()}
                return data
        except Exception as e:
            print(f"Error loading profile: {e}")
        
        return {}
    
    def list_profiles(self) -> List[Dict]:
        """
        List all saved bookmark profiles.
        
        Returns:
            List of dicts with profile info
        """
        profiles = []
        try:
            if self.PROFILES_DIR.exists():
                for filepath in self.PROFILES_DIR.glob('*.json'):
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        profiles.append({
                            'name': data.get('profile_name'),
                            'resume_name': data.get('resume_name', 'Unknown'),
                            'filename': filepath.name,
                            'bookmarks_count': len(data.get('bookmarks', [])),
                        })
        except Exception as e:
            print(f"Error listing profiles: {e}")
        
        return profiles
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a saved profile."""
        try:
            filename = re.sub(r'[^\w\s-]', '', profile_name).strip().replace(' ', '_') + '.json'
            filepath = self.PROFILES_DIR / filename
            
            if filepath.exists():
                filepath.unlink()
                print(f"✓ Profile deleted: {profile_name}")
                return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
        
        return False
    
    def validate_mapping(self, mapping: Dict[int, str], 
                        available_bookmarks: List[str]) -> Tuple[bool, str]:
        """
        Validate that a mapping uses only available bookmarks.
        
        Returns:
            (is_valid, error_message)
        """
        for cycle_num, bookmark in mapping.items():
            if bookmark not in available_bookmarks:
                return False, f"Bookmark '{bookmark}' not found in document"
        
        return True, ""
