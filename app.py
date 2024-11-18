from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TemplateMessage,
    ButtonsTemplate,
    PostbackAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    PostbackEvent,
    TextMessageContent
)
import os

app = Flask(__name__)

# 加载并验证环境变量
channel_secret = os.getenv('CHANNEL_SECRET')
if not channel_secret:
    raise ValueError("CHANNEL_SECRET 未正确配置，请检查环境变量。")

channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
if not channel_access_token:
    raise ValueError("CHANNEL_ACCESS_TOKEN 未正确配置，请检查环境变量。")

# 初始化配置
configuration = Configuration(access_token=channel_access_token)
line_handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. 请检查你的 channel access token/channel secret.")
        abort(400)

    return 'OK'

@line_handler.add(FollowEvent)
def handle_follow(event):
    print(f'Got {event.type} event')

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if event.message.text == 'postback':
            buttons_template = ButtonsTemplate(
                title='Postback Sample',
                text='Postback Action',
                actions=[
                    PostbackAction(label='Postback Action', text='Postback Action Button Clicked!', data='postback'),
                ])
            template_message = TemplateMessage(
                alt_text='Postback Sample',
                template=buttons_template
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )

@line_handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'postback':
        print('Postback event is triggered')

if __name__ == "__main__":
    app.run()
