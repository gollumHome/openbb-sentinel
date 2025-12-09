# notifier.py
import requests
import json
from config import Config


class WeChatNotifier:
    def __init__(self, webhook_url=None):
        # 优先从 Config 读取，也可以直接传参
        self.webhook_url = webhook_url if webhook_url else Config.WECHAT_WEBHOOK_URL

    def send_markdown(self, content):
        self.send(content, "markdown")

    def send_text(self, content, mentioned_mobile_list=None):
        self.send(content, "text")

    def _clean_markdown_to_text(self, md_text):
        """
        [关键辅助函数] 将 Markdown 转换为微信支持的纯文本
        """
        text = md_text
        import re

        # 1. 去掉颜色标签 <font color="xxx">Text</font> -> Text
        text = re.sub(r'<font.*?>', '', text)
        text = re.sub(r'</font>', '', text)

        # 2. 处理标题 # Title -> 【Title】
        # 将行首的 # 替换为 【，行尾加 】(简单处理)
        lines = text.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().startswith('#'):
                # 去掉 # 号，加上【】
                clean_line = line.replace('#', '').strip()
                new_lines.append(f"【{clean_line}】")
            else:
                new_lines.append(line)
        text = "\n".join(new_lines)

        # 3. 去掉加粗 **Text** -> Text
        text = text.replace('**', '')

        # 4. 去掉引用 >
        text = text.replace('> ', '')

        return text

    def send(self, content, msg_type="text"):
        """
        统一发送入口
        msg_type: "markdown" (漂亮，但仅企微可见) / "text" (丑点，但微信可见)
        """
        if not self.webhook_url:
            print("⚠️ 未配置 Webhook，跳过推送。")
            return

        headers = {"Content-Type": "application/json"}
        data = {}

        if msg_type == "markdown":
            # 只有企业微信APP能看到
            data = {
                "msgtype": "markdown",
                "markdown": {"content": content}
            }
        else:
            # 🔥 默认模式：转换为纯文本，确保个人微信能看！
            clean_content = self._clean_markdown_to_text(content)
            data = {
                "msgtype": "text",
                "text": {
                    "content": clean_content,
                    # 可以选择 @all 提醒所有人
                    # "mentioned_mobile_list": ["@all"]
                }
            }

        try:
            response = requests.post(self.webhook_url, headers=headers, data=json.dumps(data))
            # 简单的错误处理
            if response.status_code != 200:
                print(f"❌ 推送失败: {response.text}")
        except Exception as e:
            print(f"❌ 网络错误: {e}")