from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage  # 使用 TextMessage 代替 TextMessageContent
)
from linebot.v3.webhooks import (
    MessageEvent
)
import os
import re

# 初始化 Flask 应用
app = Flask(__name__)

# 从环境变量中读取 LINE Bot 的访问令牌和密钥
configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKE'))  # 确保环境变量的名称正确
line_bot_api = MessagingApi(configuration)

line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))  # 使用 CHANNEL_SECRET 环境变量

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    # 检查用户输入是否包含“计算”或“运算”
    if "计算" in text or "运算" in text:
        # 使用正则表达式来检测并执行简单的算式
        pattern = r'(\d+)\s*([\+\-\*/])\s*(\d+)'
        match = re.match(pattern, text)

        if match:
            num1, operator, num2 = match.groups()
            num1, num2 = float(num1), float(num2)

            # 进行运算
            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 != 0:
                    result = num1 / num2
                else:
                    result = '除数不能为零'

            reply = str(result)
        else:
            reply = "请输入有效的算式，如：3 + 5"
    else:
        reply = "请使用 '计算' 或 '运算' 来触发计算功能。"

    # 发送回复消息
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]  # 使用 TextMessage 发送回复
        )
    )

# Vercel 环境支持，无需使用 app.run()
def handler_function(request):
    return app(request)
