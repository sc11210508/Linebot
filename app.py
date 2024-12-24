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
    MessageImagemapAction,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
import re

app = Flask(__name__)

# 配置 Line Bot 密钥
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
    text = event.message.text.strip()
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        reply_message = None

        # 血压功能
        if "子癲前症的風險預測" in text:
            reply_message = TextMessage(text="請輸入收縮壓/舒張壓 (例：100/80)")

        elif re.match(r"^\d{2,3}/\d{2,3}$", text):  # 检测血压格式
            systolic, diastolic = map(int, text.split('/'))
            if systolic < 120 and diastolic < 80:
                reply_message = TextMessage(text="您的血壓於健康範圍內，請繼續保持！")
            elif systolic >= 140 or diastolic >= 90:
                reply_message = TextMessage(text="您的血壓過高，請立即洽詢專業醫師評估是否有現子癲前症的風險！")
            else:
                reply_message = TextMessage(text="您的血壓稍高或稍低，建議監測並與醫師討論。")

        # 妊娠糖尿功能
        elif "預防妊娠糖尿" in text:
            reply_message = TextMessage(text="請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)")

        elif re.match(r"^\d+/\d+(\.\d+)?/\d+(\.\d+)?$", text):  # 检测妊娠糖尿输入格式
            data = list(map(float, text.split('/')))
            fetus_count, bmi, weight_gain = data

            if fetus_count > 3:  # 检测是否超过三胎
                reply_message = TextMessage(text="目前只支援三胎，請聯繫專業醫師獲取建議！")
            else:
                weight_limits = None
                status_message = ""

                if fetus_count == 1:  # 单胎
                    if bmi < 18.5:
                        weight_limits = (12.7, 18.2)
                        status_message = "您的孕前 體重 過輕"
                    elif 18.5 <= bmi < 24:
                        weight_limits = (11.2, 15.9)
                        status_message = "您的孕前 體重 正常"
                    elif 24 <= bmi < 27:
                        weight_limits = (6.8, 11.3)
                        status_message = "您的孕前 體重 過重"
                    else:
                        weight_limits = (6.8, 6.8)
                        status_message = "您的孕前 體重 肥胖"
                elif fetus_count == 2:  # 双胞胎
                    weight_limits = (15.9, 20.4)
                    status_message = "您目前為雙胞胎"
                elif fetus_count == 3:  # 三胞胎
                    weight_limits = (20.4, 25.0)
                    status_message = "您目前為三胞胎"

                if weight_limits:
                    max_gain = weight_limits[1]
                    excess_weight = weight_gain - max_gain
                    if excess_weight > 0:
                        reply_message = TextMessage(
                            text=f"{status_message}，增加體重超過上限 {max_gain:.1f}kg，請注意飲食攝取，並洽詢專業醫師評估是否有現妊娠糖尿的風險！"
                        )
                    else:
                        reply_message = TextMessage(
                            text=f"{status_message}，建議增加體重範圍為 {weight_limits[0]:.1f}~{weight_limits[1]:.1f}kg，您目前的體重變化符合健康標準，請繼續保持！"
                        )

        # 推薦影片功能
        elif "推薦影片" in text:
            imagemap_base_url = request.url_root + 'static/image'
            imagemap_base_url = imagemap_base_url.replace("http://", "https://")
            video_url = request.url_root + 'static/videopr.mp4'
            video_url = video_url.replace("http://", "https://")
            preview_image_url = request.url_root + 'static/background.jpg'
            preview_image_url = preview_image_url.replace("http://", "https://")

            imagemap_message = ImagemapMessage(
                base_url=imagemap_base_url,
                alt_text='推薦影片',
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
            reply_message = imagemap_message

       
        # 回复消息
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply_message]
            )
        )

if __name__ == "__main__":
    app.run()
