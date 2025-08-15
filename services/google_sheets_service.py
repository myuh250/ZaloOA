import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleSheetsService:
    """Service to interact with Google Sheets as database"""
    
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials_file = os.getenv('CREDENTIALS_FILE', 'credentials.json')
        self.sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'ZaloOA Users')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.worksheet_name = os.getenv('WORKSHEET_NAME', 'UserStatus')
        
        # Initialize connection
        self._init_connection()
        self._init_worksheet()
    
    def _init_connection(self):
        """Initialize Google Sheets connection"""
        try:
            json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not json_str:
                raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set in environment")
            
            info = json.loads(json_str)
            creds = Credentials.from_service_account_info(info, scopes=self.scopes)
            self.gc = gspread.authorize(creds)
            print("✅ Google Sheets connection established")
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheets: {e}")
            raise
    
    def _init_worksheet(self):
        """Initialize or create worksheet"""
        try:
            if self.sheet_id:
                # Open by ID
                self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            else:
                # Open by name
                self.spreadsheet = self.gc.open(self.sheet_name)
            
            self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                
        except Exception as e:
            print(f"❌ Failed to initialize worksheet: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data from sheet"""
        try:
            records = self.worksheet.get_all_records()
            for record in records:
                if str(record.get('id')) == str(user_id):
                    return record
            return None
        except Exception as e:
            print(f"❌ Error getting user {user_id}: {e}")
            return None
        
    def get_all_users(self) -> List[Dict]:
        """Get all users from sheet"""
        try:
            return self.worksheet.get_all_records()
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []
    
    def add_user(self, user_id: str, username: str, form_status: str = 'pending') -> bool:
        """Add new user to sheet"""
        now = datetime.now().isoformat()
        row_data = [
            user_id,
            username,
            form_status,
            '',  # form_submitted_at
            '',  # last_follow_up_sent
            now  # created_at
        ]
        self.worksheet.append_row(row_data)
        return True
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user data in sheet"""
        records = self.worksheet.get_all_records()
        for i, record in enumerate(records):
            if str(record.get('id')) == str(user_id):
                row_num = i + 2  # +2 because of header and 1-based indexing
                
                # Update specific fields using update_cell for better reliability
                if 'username' in kwargs:
                    self.worksheet.update_cell(row_num, 2, kwargs['username'])
                if 'form_status' in kwargs:
                    self.worksheet.update_cell(row_num, 3, kwargs['form_status'])
                if 'form_submitted_at' in kwargs:
                    self.worksheet.update_cell(row_num, 4, kwargs['form_submitted_at'])
                if 'last_follow_up_sent' in kwargs:
                    self.worksheet.update_cell(row_num, 5, kwargs['last_follow_up_sent'])
          
        return True
    
    def sync_form_responses(self, response_sheet_name="UserStatus"):
        response_ws = self.spreadsheet.worksheet(response_sheet_name)
        responses = response_ws.get_all_records()
        
        all_users = self.get_all_users()
        
        username_to_userid = {}
        for user in all_users:
            username = user.get("username")
            if username:
                username_to_userid[username] = user.get("id")
        
        updated_users = []
        for response in responses:
            username = response.get("username")
            if not username:
                continue
                
            if username in username_to_userid:
                user_id = username_to_userid[username]
                user_data = self.get_user(user_id)
                if user_data and user_data.get("form_status") != "submitted":
                    success = self.mark_form_submitted(user_id)
                    
                    if success:
                        updated_users.append(username)
                        print(f"Updated {username} to submitted")
                        
        return updated_users
    
    def mark_form_submitted(self, user_id: str) -> bool:
        """Mark user form as submitted"""
        now = datetime.now().isoformat()
        return self.update_user(
            user_id, 
            form_status='submitted', 
            form_submitted_at=now
        )
    
    def mark_follow_up_sent(self, user_id: str) -> bool:
        """Mark follow-up as sent"""
        now = datetime.now().isoformat()
        return self.update_user(user_id, last_follow_up_sent=now)
    
    def get_all_users(self) -> List[Dict]:
        """Get all users from sheet"""
        return self.worksheet.get_all_records()
    
    def get_users_by_status(self, status: str) -> List[Dict]:
        """Get users by form status"""
        all_users = self.get_all_users()
        return [user for user in all_users if user.get('form_status') == status]

# Global instance
sheets_service = None

def get_sheets_service():
    """Get Google Sheets service instance"""
    global sheets_service
    if sheets_service is None:
        sheets_service = GoogleSheetsService()
    return sheets_service
