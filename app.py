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
    TextMessage,
    MessageImagemapAction
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent  # 修正匯入模組位置
)
import os
import re

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

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip().lower()  # 处理文本，统一转为小写

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 检查用户状态
        if user_id in user_states:
            state = user_states[user_id]
            if state == "blood_pressure":
                # 处理血压输入
                if re.match(r'^\d+/\d+$', text):
                    systolic, diastolic = map(int, text.split('/'))
                    if systolic < 90 or diastolic < 60:
                        reply_text = f"您的血壓為 {systolic}/{diastolic}，屬於偏低範圍，建議適當補充水分並注意休息。"
                    elif 90 <= systolic <= 120 and 60 <= diastolic <= 80:
                        reply_text = f"您的血壓為 {systolic}/{diastolic}，於健康範圍內，請繼續保持。"
                    elif 120 < systolic <= 140 or 80 < diastolic <= 90:
                        reply_text = f"您的血壓為 {systolic}/{diastolic}，略高於正常範圍，建議注意飲食及適當運動。"
                    else:
                        reply_text = (
                            f"您的血壓為 {systolic}/{diastolic}，偏高，孕期血壓過高可能有子癲前症風險，請立即洽詢醫師。"
                        )
                else:
                    reply_text = "請輸入正確格式的血壓數據 (例：120/80)。"
                user_states.pop(user_id)
            elif state == "gestational_diabetes":
                # 处理妊娠糖尿输入
                if re.match(r'^\d+/\d+(\.\d+)?/\d+(\.\d+)?$', text):
                    fetus_count, bmi, weight_gain = map(float, text.split('/'))
                    exceeded_weight = 0  # 超出体重默认值
                    if fetus_count == 1:  # 单胎
                        if bmi < 18.5:
                            max_gain = 18.2
                            recommended = "12.7~18.2 kg"
                        elif 18.5 <= bmi < 24:
                            max_gain = 15.9
                            recommended = "11.2~15.9 kg"
                        elif 24 <= bmi < 27:
                            max_gain = 11.3
                            recommended = "6.8~11.3 kg"
                        else:  # bmi >= 27
                            max_gain = 6.8
                            recommended = "最多6.8 kg"
                        if weight_gain > max_gain:
                            exceeded_weight = weight_gain - max_gain
                            reply_text = (
                                f"您目前為單胞胎，建議增加體重範圍為 {recommended}。\n"
                                f"您已超出建議上限 {exceeded_weight:.1f} kg，請注意飲食攝取，並洽詢醫師評估是否有妊娠糖尿的風險。"
                            )
                        else:
                            reply_text = f"您目前為單胞胎，建議增加體重範圍為 {recommended}，目前體重增加正常，請繼續保持。"
                    elif fetus_count == 2:  # 双胞胎
                        max_gain = 20.4
                        if weight_gain > max_gain:
                            exceeded_weight = weight_gain - max_gain
                            reply_text = (
                                f"您目前為雙胞胎，建議增加體重範圍為 15.9~20.4 kg。\n"
                                f"您已超出建議上限 {exceeded_weight:.1f} kg，請洽詢醫師評估是否有妊娠糖尿的風險。"
                            )
                        else:
                            reply_text = "您目前為雙胞胎，建議增加體重範圍為 15.9~20.4 kg，請繼續保持。"
                    elif fetus_count == 3:  # 三胞胎
                        max_gain = 25.0
                        if weight_gain > max_gain:
                            exceeded_weight = weight_gain - max_gain
                            reply_text = (
                                f"您目前為三胞胎，建議增加體重範圍為 20.4~25.0 kg。\n"
                                f"您已超出建議上限 {exceeded_weight:.1f} kg，請洽詢醫師評估是否有妊娠糖尿的風險。"
                            )
                        else:
                            reply_text = "您目前為三胞胎，建議增加體重範圍為 20.4~25.0 kg，請繼續保持。"
                    else:
                        reply_text = "胎數不支援超過三胎，請洽詢醫師獲取專業建議。"
                else:
                    reply_text = "請輸入正確格式 (例：1/25/5)。"
                user_states.pop(user_id)
            else:
                reply_text = "目前未處於任何狀態，請輸入正確的關鍵字。"
        else:
            # 自动识别关键字
            if '子癲前症的風險預測' in text:
                reply_text = "請輸入您的血壓數據 (例：120/80)。"
                user_states[user_id] = "blood_pressure"
            elif '妊娠糖尿風險預測' in text or '體重' in text:
                reply_text = "請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)。"
                user_states[user_id] = "gestational_diabetes"
            
        # 回复消息
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
    


if __name__ == "__main__":
    app.run(debug=True)
