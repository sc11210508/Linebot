const express = require('express');
const { Client, middleware } = require('@line/bot-sdk');

// 環境變數設定
const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKE,
  channelSecret: process.env.CHANNEL_SECRET,
};
const app = express();

// LINE 的 Middleware
app.use(middleware(config));

// 接收 LINE 的 Webhook 請求
app.post('/callback', (req, res) => {
  Promise.all(req.body.events.map(handleEvent))
    .then((result) => res.json(result))
    .catch((err) => {
      console.error(err);
      res.status(500).end();
    });
});

// 處理事件
const client = new Client(config);
async function handleEvent(event) {
  if (event.type !== 'message' || event.message.type !== 'text') {
    return Promise.resolve(null);
  }

  const userInput = event.message.text.trim();
  let replyMessage = '';

  if (userInput === '1') {
    replyMessage = '請輸入收縮壓/舒張壓 (例：100/80)';
  } else if (userInput.match(/^\d+\/\d+$/)) {
    const [systolic, diastolic] = userInput.split('/').map(Number);
    if (systolic < 140 && diastolic < 90) {
      replyMessage = '您的血壓於健康範圍內，請繼續保持';
    } else {
      replyMessage = '您的孕期血壓過高，請立即洽詢專業醫師評估是否有現子癲前症的風險';
    }
  } else if (userInput === '2') {
    replyMessage = '請輸入胎數/孕前BMI/孕前至今增加的體重 (例：1/25/5)';
  } else if (userInput.match(/^\d+\/\d+\/\d+$/)) {
    const [fetuses, bmi, weightGain] = userInput.split('/').map(Number);
    const weightGainLimit = fetuses === 1 && bmi >= 25 ? 11.3 : 15.9;

    if (weightGain <= weightGainLimit) {
      replyMessage = `您目前為單胞胎，孕前BMI略高，增加體重上限為${weightGainLimit}KG`;
    } else {
      replyMessage = `您目前為單胞胎，孕前BMI略高，增加體重超過上限${weightGainLimit}KG，請注意飲食攝取，並洽詢專業醫師評估是否有現妊娠糖尿的風險`;
    }
  } else {
    replyMessage = '請輸入 1 或 2 開始測試。';
  }

  return client.replyMessage(event.replyToken, {
    type: 'text',
    text: replyMessage,
  });
}

// 啟動伺服器
const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
