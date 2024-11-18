from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os

app = Flask(__name__)

# 使用环境变量加载密钥（推荐）
channel_secret = os.getenv('CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')

if not channel_secret or not channel_access_token:
    raise ValueError("CHANNEL_SECRET 和 CHANNEL_ACCESS_TOKEN 必须正确配置！")

# 初始化配置
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # 获取 X-Line-Signature 请求头
    signature = request.headers.get('X-Line-Signature', '')

    # 获取请求体
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # 校验签名并处理事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature. 请检查你的 channel access token 和 channel secret 是否正确。")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 使用 Line Messaging API 回复消息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"你说了: {event.message.text}")]
            )
        )


if __name__ == "__main__":
    # 如果部署到生产环境，请修改 host 和 port 的设置
    app.run(host='0.0.0.0', port=5000)
