# notifier.py
import requests
import json
from config import Config


class WeChatNotifier:
    def __init__(self, webhook_url=None):
        # 优先从 Config 读取，也可以直接传参
        self.webhook_url = webhook_url if webhook_url else Config.WECHAT_WEBHOOK_URL

    def send_markdown(self, content):
        """
        发送 Markdown 格式的消息 (最适合 AI 报告)
        """
        if not self.webhook_url:
            print("⚠️ 未配置企业微信 Webhook，跳过推送。")
            return

        headers = {"Content-Type": "application/json"}

        # 构造企业微信要求的 JSON 数据包
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        try:
            response = requests.post(self.webhook_url, headers=headers, data=json.dumps(data))
            res_json = response.json()

            if res_json.get("errcode") == 0:
                print("✅ 消息已推送到企业微信群！")
            else:
                print(f"❌ 推送失败: {res_json}")
        except Exception as e:
            print(f"❌ 网络请求错误: {e}")

    def send_text(self, content, mentioned_mobile_list=None):
        """
        发送普通文本，支持 @某人
        mentioned_mobile_list: ["13800000000", "@all"]
        """
        if not self.webhook_url:
            return

        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_mobile_list": mentioned_mobile_list or []
            }
        }

        requests.post(self.webhook_url, json=data)