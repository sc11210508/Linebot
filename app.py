from linebot import LineBotApi, WebhookHandler
from linebot.models import TextMessage

# 替換您的 channel_access_token 和 channel_secret
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))  # 確保在環境變數中設定
line_handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))  # 同上

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

    # 判斷輸入內容
    if text == "推薦影片":
        handle_recommend_video(event)
        return

    # 血壓檢測或妊娠糖尿
    reply = handle_health_features(text)
    try:
        line_bot_api.reply_message(
            event.reply_token, TextMessage(text=reply)
        )
    except Exception as e:
        app.logger.error(f"Error sending reply: {e}")
        line_bot_api.reply_message(event.reply_token, TextMessage(text="發送訊息錯誤，請稍後再試！"))

def handle_recommend_video(event):
    # 創建推薦影片消息
    imagemap_base_url = request.url_root + 'static/image'
    video_url = request.url_root + 'static/videopr.mp4'
    preview_image_url = request.url_root + 'static/background.jpg'

    # 實現簡化的影片推薦邏輯
    video_message = ImagemapMessage(
        base_url=imagemap_base_url,
        alt_text='影片推薦',
        base_size=ImagemapBaseSize(height=1040, width=1040),
        video=ImagemapVideo(
            original_content_url=video_url,
            preview_image_url=preview_image_url,
            area=ImagemapArea(x=0, y=0, width=1040, height=520)
        ),
        actions=[MessageImagemapAction(
            text='觀看更多',
            area=ImagemapArea(x=0, y=520, width=1040, height=520)
        )]
    )

    line_bot_api.reply_message(event.reply_token, video_message)


def handle_health_features(text):
    if text.startswith("血壓"):
        try:
            bp = text.replace("血壓", "").strip()
            bp_values = bp.split("/")

            if len(bp_values) == 2:
                systolic, diastolic = int(bp_values[0]), int(bp_values[1])

                # 血壓判斷
                if systolic < 120 and diastolic < 80:
                    return "您的血壓於健康範圍內，請繼續保持"
                elif systolic >= 140 or diastolic >= 90:
                    return "您的孕期血壓過高，請立即洽詢專業醫師評估是否有現子癲前症的風險"
                else:
                    return "您的血壓接近健康範圍，請注意保持良好生活習慣"
            else:
                return "請輸入正確格式的血壓 (例：血壓 100/80)"
        except ValueError:
            return "血壓數值無效，請重新輸入正確的格式 (例：血壓 100/80)"
    
    elif text.startswith("妊娠糖尿"):
        try:
            data = text.split("/")
            if len(data) == 3:
                fetus_count, pre_bmi, weight_gain = int(data[0]), int(data[1]), int(data[2])

                # 計算體重增加上限 (假設是 11.3 kg)
                weight_limit = 11.3
                if weight_gain > weight_limit:
                    return f"您的體重已經超過預期增加上限 {weight_limit} kg，請注意飲食攝取，並洽詢專業醫師評估是否有現妊娠糖尿的風險"
                else:
                    return f"您的體重增加在正常範圍內，單胞胎孕期BMI為 {pre_bmi}，體重增加上限為 {weight_limit} kg"
            else:
                return "請輸入正確格式的數據 (例：妊娠糖尿 1/25/5)"
        except ValueError:
            return "妊娠糖尿數值無效，請重新輸入。"

    return "無法識別您的需求，請重新輸入。"


if __name__ == "__main__":
    app.run(debug=True)
