import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sympy

app = Flask(__name__)

# LineBot API 和 Webhook Handler 的設置
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # 取得訊息事件
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    # 驗證訊息並處理事件
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(e)
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # 使用 sympy 库處理數學表達式
        result = sympy.sympify(user_message)
        result = str(result)
    except Exception as e:
        result = "無法識別的表達式，請輸入有效的數學運算式。"
    
    # 回傳計算結果
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )

if __name__ == "__main__":
    app.run()

