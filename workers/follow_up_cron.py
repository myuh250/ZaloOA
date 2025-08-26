from services.form_service import get_form_service
from services.google_sheets_service import get_sheets_service
from services.bot_service import BotService
from services.bot_service import UserAction
from utils.date_convert import *
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

FOLLOW_UP_THRESHOLD = 86400  # 24 hours = 86400 seconds

# Initialize services
form_service = get_form_service()
bot_service = BotService(form_service)

async def run_sync_form_responses():
    updated_users = get_sheets_service().sync_form_responses("UserStatus")
    print("Auto synced users:", updated_users)
    all_users = get_sheets_service().get_all_users()
    
    for username in updated_users:
        user = next((u for u in all_users if u.get("username") == username), None)
        if user:
            user_id = user.get("id")
            response = bot_service.handle_completed(UserAction(
                user_id=user_id,
                user_name=username,
                action_type="completed"
            ))
    
    return updated_users
    
async def send_follow_up(user_id, user_name):
    user_action = UserAction(
        user_id=user_id,
        user_name=user_name,
        action_type="follow_up"
    )
    response = bot_service.handle_follow_up(user_action)
            
async def run_follow_up_cron():
    """
    Gửi follow-up message 1 lần/ngày cho user:
    - Chưa submit form (status = pending)
    - Đã qua 24h kể từ lần cuối follow-up
    - Đang ở stage follow_up
    """
    print("🔍 Starting daily follow-up check...")
    
    sheets = get_sheets_service()
    all_users = sheets.get_all_users()
    follow_up_sent = 0
    
    for user in all_users:
        user_id = user.get('id')  
        user_name = user.get('username', 'User')
        form_status = user.get('form_status', '')
        
        # Skip users who already submitted form
        if form_status == 'submitted':
            continue
            
        stage = form_service.get_user_stage(user_id)
        
        # Chỉ gửi follow-up cho user ở stage 'follow_up'
        if stage != 'follow_up':
            continue
            
        last_follow_up_time = user.get('last_follow_up_sent', '')
        
        # Nếu chưa từng gửi follow-up, skip (đợi user tương tác trước)
        if not last_follow_up_time:
            continue
            
        # Check 24h đã qua chưa
        last = iso_to_vn_datetime(last_follow_up_time)
        now = datetime.now(timezone(timedelta(hours=7)))
        diff = compare_datetime(now, last)
        seconds = timedelta_to_seconds(diff)
        
        if seconds and seconds > FOLLOW_UP_THRESHOLD:
            await send_follow_up(user_id, user_name)
            follow_up_sent += 1
            print(f"📨 Sent daily follow-up to {user_name} (ID: {user_id})")
        else:
            hours_left = (FOLLOW_UP_THRESHOLD - (seconds or 0)) / 3600
            print(f"⏳ {user_name}: waiting {hours_left:.1f}h more for next follow-up")
    
    print(f"✅ Daily follow-up completed: {follow_up_sent} messages sent")