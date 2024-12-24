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
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent  # 修正匯入模組位置
)
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKE'))  # 修正環境變數名稱
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 用於記錄使用者狀態
user_status = {}


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
    text = event.message.text
    user_id = event.source.user_id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 檢查使用者輸入是否為推薦影片
        if text == "推薦影片":
            handle_recommend_video(event, line_bot_api)
            return

        # 處理健康功能
        reply = handle_health_features(user_id, text)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessageContent(text=reply)]
                )
            )
        except Exception as e:
            app.logger.error(f"Error sending reply: {e}")


def handle_recommend_video(event, line_bot_api):
    # 構造靜態文件的 URL
    imagemap_base_url = request.url_root + 'static/image'
    imagemap_base_url = imagemap_base_url.replace("http://", "https://")
    video_url = request.url_root + 'static/videopr.mp4'
    video_url = video_url.replace("http://", "https://")
    preview_image_url = request.url_root + 'static/background.jpg'
    preview_image_url = preview_image_url.replace("http://", "https://")

    # 創建 ImagemapMessage
    imagemap_message = ImagemapMessage(
        base_url=imagemap_base_url,
        alt_text='this is an imagemap',
        base_size=ImagemapBaseSize(height=1040, width=1040),
        video=ImagemapVideo(
            original_content_url=video_url,
            preview_image_url=preview_image_url,
            area=ImagemapArea(
                x=0, y=0, width=1040, height=520
            ),
            external_link=ImagemapExternalLink(
                link_uri='https://www.youtube.com/@yannilife8',
                label='點我看更多',
            ),
        ),
        actions=[
            MessageImagemapAction(
                text='更多影片',
                area=ImagemapArea(
                    x=0, y=520, width=1040, height=520
                )
            )
        ]
    )

    # 发送消息
    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[imagemap_message]
            )
        )
    except Exception as e:
        app.logger.error(f"Error sending reply: {e}")


    


if __name__ == "__main__":
    app.run(debug=True)
