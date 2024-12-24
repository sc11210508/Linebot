from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessageContent
)
from linebot.v3.webhooks import (
    MessageEvent
)
import re

app = Flask(__name__)

# LINE Bot Token 和 Secret
line_bot_api = MessagingApi(Configuration(channel_access_token='YOUR_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
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
            messages=[TextMessageContent(text=reply)]
        )
    )

# 为 Vercel 适配 Flask 的调用方式
def handler_function(request):
    return app(request)

