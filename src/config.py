import os
import json
from datetime import datetime

class Config:
    """Configuration management with secure credential storage"""
    
    def __init__(self):
        self.app_name = "Petdentity Scraper"
        self.version = "1.0.0"
        self.login_url = "https://app.petdentity.com.ph/session/login"
        self.data_dir = "data"
        self.records_dir = f"{self.data_dir}/records"
        self.exports_dir = f"{self.data_dir}/exports"
        self.logs_dir = "logs"
        self.credentials_file = f"{self.data_dir}/credentials.json"
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.records_dir, self.exports_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def save_credentials(self, username, password):
        """Save credentials to file"""
        try:
            creds = {
                'username': username,
                'password': password,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.credentials_file, 'w') as f:
                json.dump(creds, f)
            # Secure on Unix
            try:
                os.chmod(self.credentials_file, 0o600)
            except:
                pass
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def load_credentials(self):
        """Load credentials from file"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                return creds.get('username'), creds.get('password')
        except Exception as e:
            print(f"Error loading credentials: {e}")
        return None, None
    
    def clear_credentials(self):
        """Clear saved credentials"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                return True
        except Exception as e:
            print(f"Error clearing credentials: {e}")
        return False