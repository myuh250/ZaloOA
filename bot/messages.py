START_TEXT = "Xin chào! Cảm ơn bạn đã kết nối cùng chúng tôi."
FORM_PROMPT = "Vui lòng nhấn vào link bên dưới để bổ sung thông tin:"
BUTTON_FILLED = "Tôi đã điền form"
THANK_YOU = "Cảm ơn bạn! Chúng tôi đã nhận được thông tin."

WELCOME_MESSAGE = "Chào mừng bạn đến với bot của chúng tôi! Đây là lần đầu tiên bạn sử dụng dịch vụ."
WELCOME_CTA = "Bắt đầu"
AFTER_INTERACTION_MESSAGE = "Cảm ơn bạn đã tương tác! Chúng tôi rất vui được phục vụ bạn. Dưới đây là thông tin tiếp theo:"

import requests 
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_URL_V3 = "https://openapi.zalo.me/v3.0/" 

def send_text_message(ZALO_OA_ACCESS_TOKEN, user_id, message_text=None, message_file=None):
    url = API_URL_V3 + "message/cs"
    headers = {
        "Content-Type": "application/json",
        "access_token": ZALO_OA_ACCESS_TOKEN
    }
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {}
    }

    if message_text and message_file:
        raise ValueError("Both message_text and message_file cannot be provided at the same time")
    elif message_text:
        data["message"]["text"] = message_text
    elif message_file:
        with open(message_file, "r") as f:
            data["message"]["text"] = f.read()
    else:
        raise ValueError("Either message_text or message_file must be provided")

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return print(response.json())