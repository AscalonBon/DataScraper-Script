import re
from datetime import datetime

class Utils:
    """Utility functions for the application"""
    
    @staticmethod
    def clean_text(text):
        """Clean and normalize text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def extract_phone(text):
        """Extract phone number from text"""
        if not text:
            return None
        match = re.search(r'(\d{11,13})', text)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_date(text):
        """Extract date from text"""
        if not text:
            return None
        patterns = [
            r'([A-Za-z]{3}\s\d{2},\s\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def format_datetime():
        """Get formatted current datetime"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    @staticmethod
    def generate_filename(prefix, extension='json'):
        """Generate a unique filename with timestamp"""
        timestamp = Utils.format_datetime()
        return f"{prefix}_{timestamp}.{extension}"