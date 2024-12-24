from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,  # 使用 TextMessage
    ImagemapArea,
    ImagemapBaseSize,
    ImagemapExternalLink,
    ImagemapMessage,
    ImagemapVideo,
    MessageImagemapAction
)
from linebot.v3.webhooks import MessageEvent
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKE'))  # 確保環境變數名稱正確
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


@line_handler.add(MessageEvent, message=TextMessage)  # 使用 TextMessage 來處理訊息
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
                    messages=[TextMessage(text=reply)]  # 使用 TextMessage 來回覆訊息
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


def handle_health_features(user_id, text):
    # 處理血壓檢測或妊娠糖尿風險的邏輯
    if text == "血壓":
        return "請輸入收縮壓/舒張壓 (例：100/80)"
    elif text == "妊娠糖尿風險":
        return "請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)"
    else:
        return "無法識別您的請求，請再試一次"

if __name__ == "__main__":
    app.run(debug=True)

