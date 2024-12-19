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


def generate_secure_url(resource_path):
    url = request.url_root + resource_path
    return url.replace("http://", "https://")


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
    imagemap_base_url = generate_secure_url('static/image')
    video_url = generate_secure_url('static/videopr.mp4')
    preview_image_url = generate_secure_url('static/background.jpg')

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

    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[imagemap_message]
            )
        )
    except Exception as e:
        app.logger.error(f"Error sending imagemap reply: {e}")


def handle_health_features(user_id, text):
    if user_id not in user_status:
        if "血壓" in text:
            reply = "請輸入收縮壓/舒張壓 (例：100/80)"
            user_status[user_id] = "awaiting_blood_pressure"
        elif "妊娠糖尿" in text:
            reply = "請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)"
            user_status[user_id] = "awaiting_gdm_data"
        else:
            reply = "請輸入以下關鍵字或選項：\n1. 血壓\n2. 預防妊娠糖尿\n或直接輸入 '推薦影片' 獲取相關資訊。"
            user_status[user_id] = "awaiting_choice"
    elif user_status[user_id] == "awaiting_choice":
        if text == "1":
            reply = "請輸入收縮壓/舒張壓 (例：100/80)"
            user_status[user_id] = "awaiting_blood_pressure"
        elif text == "2":
            reply = "請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)"
            user_status[user_id] = "awaiting_gdm_data"
        else:
            reply = "請輸入正確的選項：1 或 2。"
    elif user_status[user_id] == "awaiting_blood_pressure":
        try:
            systolic, diastolic = map(int, text.split("/"))
            if systolic < 120 and diastolic < 80:
                reply = f"您的血壓於健康範圍內，請繼續保持 ({systolic}/{diastolic})。"
            elif systolic >= 140 or diastolic >= 90:
                reply = f"您的孕期血壓過高 ({systolic}/{diastolic})，請立即洽詢專業醫師評估是否有現子癲前症的風險。"
            else:
                reply = f"您的血壓略高，建議保持觀察並注意飲食與休息 ({systolic}/{diastolic})。"
        except:
            reply = "輸入格式錯誤，請重新輸入收縮壓/舒張壓 (例：100/80)。"
        user_status[user_id] = None
    elif user_status[user_id] == "awaiting_gdm_data":
        try:
            fetus_count, pre_bmi, weight_gain = map(float, text.split("/"))
            if fetus_count == 1:
                if pre_bmi < 18.5:
                    limit = 18
                elif 18.5 <= pre_bmi < 24.9:
                    limit = 16
                else:
                    limit = 11.3
            elif fetus_count == 2:
                limit = 20  # 雙胞胎的基本上限
            else:
                reply = "目前僅支援單胞胎或雙胞胎數據評估。"
                limit = None

            if limit:
                if weight_gain > limit:
                    reply = f"您目前為單胞胎，孕前BMI為 {pre_bmi}，增加體重超過上限 {limit}KG，請注意飲食並洽詢專業醫師評估妊娠糖尿風險。"
                else:
                    reply = f"您目前為單胞胎，孕前BMI為 {pre_bmi}，體重增加在合理範圍內，請繼續保持。"
        except:
            reply = "輸入格式錯誤，請重新輸入胎數/孕前BMI/體重增加 (例：1/25/5)。"
        user_status[user_id] = None
    else:
        reply = "請選擇要進行的功能：\n1. 血壓\n2. 預防妊娠糖尿"
        user_status[user_id] = "awaiting_choice"
    return reply


if __name__ == "__main__":
    app.run(debug=True)
