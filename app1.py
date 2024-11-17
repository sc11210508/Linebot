from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    ImagemapArea,
    ImagemapBaseSize,
    ImagemapExternalLink,
    ImagemapMessage,
    ImagemapVideo,
    MessageImagemapAction
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os

# 设置编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 检查环境变量
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("CHANNEL_ACCESS_TOKEN 或 CHANNEL_SECRET 未设置！")

# Flask 和 LINE 配置
app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
linehandler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        linehandler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@linehandler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if text == '推薦影片':
            imagemap_base_url = request.url_root + '/static/image'
            imagemap_base_url = imagemap_base_url.replace("http", "https")
            video_url = request.url_root + '/static/videopr.mp4'
            video_url = video_url.replace("http", "https")
            preview_image_url = request.url_root + '/static/background.jpg'
            preview_image_url = preview_image_url.replace("http", "https")

            imagemap_message = ImagemapMessage(
                base_url=imagemap_base_url,
                alt_text='this is an imagemap',
                base_size=ImagemapBaseSize(height=1040, width=1040),
                video=ImagemapVideo(
                    original_content_url=video_url,
                    preview_image_url=preview_image_url,
                    area=ImagemapArea(x=0, y=0, width=1040, height=520),
                    external_link=ImagemapExternalLink(
                        link_uri='https://www.youtube.com/@yannilife8',
                        label='點我看更多',
                    ),
                ),
                actions=[
                    MessageImagemapAction(
                        text='更多影片',
                        area=ImagemapArea(x=0, y=520, width=1040, height=520)
                    )
                ]
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[imagemap_message]
                )
            )


if __name__ == "__main__":
    app.run()