from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import os

# 初始化 LINE Bot API 和 WebhookHandler
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "oscjo4bj4"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 初始化 Flask
app = Flask(__name__)

# 主頁
@app.route('/')
def home():
    return 'Hello, World!'

# Webhook 路徑，LINE 將發送 POST 請求到這裡
@app.route("/webhook", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']
    
    # 獲取請求的原始內容
    body = request.get_data(as_text=True)
    
    app.logger.info("Request body: " + body)
    
    # 處理 webhook 請求
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

# 當收到訊息時處理
@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 根據訊息進行回應
    if user_message == '血壓':
        text_message = TextSendMessage(text="請輸入收縮壓/舒張壓 (例：100/80)")
        line_bot_api.reply_message(event.reply_token, text_message)

    elif '/' in user_message:  # 假設格式為收縮壓/舒張壓
        try:
            systolic, diastolic = map(int, user_message.split('/'))
            
            if systolic < 120 and diastolic < 80:
                text_message = TextSendMessage(text="您的血壓於健康範圍內，請繼續保持")
            elif systolic >= 140 or diastolic >= 90:
                text_message = TextSendMessage(text="您的孕期血壓過高，請立即洽詢專業醫師評估是否有現子癲前症的風險")
            else:
                text_message = TextSendMessage(text="您的血壓正常範圍內，請繼續保持")

            line_bot_api.reply_message(event.reply_token, text_message)
        except ValueError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入有效的血壓數值（例如：100/80）"))

    elif user_message == '預防妊娠糖尿':
        text_message = TextSendMessage(text="請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)")
        line_bot_api.reply_message(event.reply_token, text_message)

    elif '/' in user_message:  # 假設格式為 胎數/BMI/體重
        try:
            fetus_count, pre_bmi, weight_gain = map(int, user_message.split('/'))
            
            weight_limit = 11.3  # 這是示例數值，可以根據需要調整
            if weight_gain > weight_limit:
                text_message = TextSendMessage(text="孕前BMI略高，體重超過上限，請注意飲食攝取，並洽詢專業醫師評估是否有現妊娠糖尿的風險")
            else:
                text_message = TextSendMessage(text="孕前BMI略高，增加體重上限為11.3KG")
            
            line_bot_api.reply_message(event.reply_token, text_message)
        except ValueError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入有效的數值（例如：1/25/5）"))

# 設定主程式運行
if __name__ == "__main__":
    app.run(debug=True, port=5000)
