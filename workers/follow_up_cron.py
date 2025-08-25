from services.form_service import get_form_service
from services.google_sheets_service import get_sheets_service
from services.bot_service import BotService
from services.bot_service import UserAction
from utils.date_convert import *
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

FOLLOW_UP_THRESHOLD = 3600

# Initialize services
form_service = get_form_service()
bot_service = BotService(form_service)

async def run_sync_form_responses():
    updated_users = get_sheets_service().sync_form_responses("UserStatus")
    print("Auto synced users:", updated_users)
    all_users = get_sheets_service().get_all_users()
    
    # Import ZaloMessagingGateway for sending messages
    from adapters.zalo_messaging_gateway import ZaloMessagingGateway
    zalo_gateway = ZaloMessagingGateway()
    
    for username in updated_users:
        user = next((u for u in all_users if u.get("username") == username), None)
        if user:
            user_id = user.get("id")
            response = bot_service.handle_completed(UserAction(
                user_id=user_id,
                user_name=username,
                action_type="completed"
            ))
            # Send thank you message via Zalo
            await zalo_gateway.send_response(response, str(user_id))
            print(f"Completion message sent to {username} (ID: {user_id}): {response.text}")
    
    # Return the updated_users list for the API to use
    return updated_users
    
async def send_follow_up(user_id, user_name):
    user_action = UserAction(
        user_id=user_id,
        user_name=user_name,
        action_type="follow_up"
    )
    response = bot_service.handle_follow_up(user_action)
    
    # Send follow-up message via Zalo
    from adapters.zalo_messaging_gateway import ZaloMessagingGateway
    zalo_gateway = ZaloMessagingGateway()
    await zalo_gateway.send_response(response, str(user_id))
    print(f"Follow-up message sent to {user_name} (ID: {user_id}): {response.text}")
            
async def run_follow_up_cron():
    sheets = get_sheets_service()
    all_users = sheets.get_all_users()
    for user in all_users:
        user_id = user.get('id')  
        user_name = user.get('username', 'User') 
        stage = form_service.get_user_stage(user_id)
        # print(f"Checking user {user_name} (ID: {user_id}), stage: {stage}")
        
        if stage != 'follow_up':
            continue
            
        last_follow_up_time = user.get('last_follow_up_sent', '')
        last = iso_to_vn_datetime(last_follow_up_time)
        now = datetime.now(timezone(timedelta(hours=7)))
        diff = compare_datetime(now, last)
        seconds = timedelta_to_seconds(diff)
        
        if seconds is None:
            # User has never been followed up so we don't send anything based on requirements
            continue
        elif seconds > FOLLOW_UP_THRESHOLD:
            await send_follow_up(user_id, user_name)
            print(f"Sent follow-up to {user_name} (ID: {user_id})")
        else:
            print(f"Waiting, only {seconds}s passed (need {FOLLOW_UP_THRESHOLD}s)")