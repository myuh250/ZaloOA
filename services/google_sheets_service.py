import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
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
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=self.scopes
            )
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
            # Use expected headers to avoid duplicate empty header issue
            expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
            records = self.worksheet.get_all_records(expected_headers=expected_headers)
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
            # Use expected headers to avoid duplicate empty header issue
            expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
            return self.worksheet.get_all_records(expected_headers=expected_headers)
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []
    
    def add_user(self, user_id: str, username: str, form_status: str = 'pending') -> bool:
        """Add new user to sheet"""
        now = datetime.now().isoformat()
        row_data = [
            user_id,
            username,
            '',  # name (empty initially)
            '',  # email (empty initially)
            form_status,
            '',  # form_submitted_at
            '',  # last_follow_up_sent
            now  # created_at
        ]
        self.worksheet.append_row(row_data)
        return True
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user data in sheet"""
        try:
            # Get actual headers to find correct column positions
            actual_headers = self.worksheet.row_values(1)
            
            # Create mapping of field to actual column number
            field_to_col = {}
            target_fields = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
            
            for field in target_fields:
                try:
                    col_index = actual_headers.index(field) + 1  # +1 for 1-based indexing
                    field_to_col[field] = col_index
                except ValueError:
                    print(f"⚠️  Field '{field}' not found in headers: {actual_headers}")
            
            # Find user row using expected headers for clean data
            expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
            records = self.worksheet.get_all_records(expected_headers=expected_headers)
            
            for i, record in enumerate(records):
                if str(record.get('id')) == str(user_id):
                    row_num = i + 2  # +2 because of header and 1-based indexing
                    
                    # Update fields using actual column positions
                    if 'username' in kwargs and 'username' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['username'], kwargs['username'])
                    if 'name' in kwargs and 'name' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['name'], kwargs['name'])
                    if 'email' in kwargs and 'email' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['email'], kwargs['email'])
                    if 'form_status' in kwargs and 'form_status' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['form_status'], kwargs['form_status'])
                    if 'form_submitted_at' in kwargs and 'form_submitted_at' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['form_submitted_at'], kwargs['form_submitted_at'])
                    if 'last_follow_up_sent' in kwargs and 'last_follow_up_sent' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['last_follow_up_sent'], kwargs['last_follow_up_sent'])
                    if 'created_at' in kwargs and 'created_at' in field_to_col:
                        self.worksheet.update_cell(row_num, field_to_col['created_at'], kwargs['created_at'])
                    
                    print(f"✅ Updated user {user_id} in row {row_num} using columns: {field_to_col}")
                    return True
            
            print(f"❌ User {user_id} not found in records")
            return False
            
        except Exception as e:
            print(f"❌ Error updating user {user_id}: {e}")
            return False
    
    def sync_form_responses(self, response_sheet_name="UserStatus"):
        response_ws = self.spreadsheet.worksheet(response_sheet_name)
        # Use expected headers for response sheet too
        expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
        responses = response_ws.get_all_records(expected_headers=expected_headers)
        
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
    
    def update_user_info(self, user_id: str, name: str = None, email: str = None) -> bool:
        """Update user's name and email information"""
        updates = {}
        if name is not None:
            updates['name'] = name
        if email is not None:
            updates['email'] = email
        
        if updates:
            return self.update_user(user_id, **updates)
        return True
    
    def has_complete_user_info(self, user_id: str) -> bool:
        """Check if user has both name and email filled"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        name = user.get('name', '').strip()
        email = user.get('email', '').strip()
        
        return bool(name) and bool(email)
    
    def get_users_by_status(self, status: str) -> List[Dict]:
        """Get users by form status"""
        all_users = self.get_all_users()
        return [user for user in all_users if user.get('form_status') == status]
    
    def debug_sheet_structure(self):
        """Debug method to check sheet structure"""
        try:
            print("=== DEBUGGING SHEET STRUCTURE ===")
            
            # Get header row
            header_values = self.worksheet.row_values(1)
            print(f"📋 Headers: {header_values}")
            
            # Get first few rows
            all_values = self.worksheet.get_all_values()
            print(f"📊 Total rows: {len(all_values)}")
            
            if len(all_values) > 1:
                print("📝 First data row:", all_values[1])
            
            # Get records with header mapping using expected headers
            expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
            records = self.worksheet.get_all_records(expected_headers=expected_headers)
            if records:
                print(f"🔍 First record keys: {list(records[0].keys())}")
                print(f"🔍 First record: {records[0]}")
                
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            
        return {"headers": header_values if 'header_values' in locals() else []}
    
    def fix_headers_if_needed(self):
        """Fix headers to match expected format"""
        expected_headers = ['id', 'username', 'name', 'email', 'form_status', 'form_submitted_at', 'last_follow_up_sent', 'created_at']
        
        try:
            current_headers = self.worksheet.row_values(1)
            print(f"Current headers: {current_headers}")
            print(f"Expected headers: {expected_headers}")
            
            if current_headers != expected_headers:
                print("🔧 Updating headers...")
                # Update header row
                for i, header in enumerate(expected_headers, 1):
                    self.worksheet.update_cell(1, i, header)
                print("✅ Headers updated!")
                return True
            else:
                print("✅ Headers already correct!")
                return True
                
        except Exception as e:
            print(f"❌ Failed to fix headers: {e}")
            return False

# Global instance
sheets_service = None

def get_sheets_service():
    """Get Google Sheets service instance"""
    global sheets_service
    if sheets_service is None:
        sheets_service = GoogleSheetsService()
    return sheets_service
