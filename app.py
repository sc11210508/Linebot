from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKE'))
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip().replace("　", " ")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if "血壓" in text:
            reply = "請輸入收縮壓/舒張壓 (例：100/80)"
        elif "妊娠糖尿" in text:
            reply = "請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)"
        else:
            reply = "無法辨識您的需求，請輸入 '血壓' 或 '妊娠糖尿' 獲取相關資訊。"

        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessageContent(text=reply)]
                )
            )
        except Exception as e:
            app.logger.error(f"Error sending reply: {e}")

if __name__ == "__main__":
    app.run(debug=True)
