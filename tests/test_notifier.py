# test_notifier.py
from notifier import WeChatNotifier
from config import Config
import time


def test_push():
    print("🚀 开始测试企业微信推送...")

    # 1. 初始化
    # 如果你的 config.py 里已经填了 URL，这里可以直接用 WeChatNotifier()
    # 如果还没填，可以临时在这里传入: WeChatNotifier(webhook_url="你的https://...")
    notifier = WeChatNotifier()

    if not notifier.webhook_url:
        print("❌ 错误: 未找到 Webhook URL，请检查 config.py 或在初始化时传入。")
        return

    # 2. 测试 Markdown 消息 (最常用)
    print("Testing Markdown...")
    markdown_content = """
# 📢 报警测试: OpenBB-Sentinel
<font color="info">✅ 连接状态: 正常</font>
<font color="warning">⚠️ 风险提示: 波动率上升</font>
<font color="comment">📅 时间: 2025-12-09</font>

### 详细数据:
- **RSI**: 65.4 (强势)
- **价格**: $124.5
- [点击查看详情](https://www.google.com)

> 这是来自 Python 脚本的测试消息
    """
    notifier.send_markdown(markdown_content)

    # 休息一下，防止发送太快
    time.sleep(1)

    # 3. 测试普通文本 + @所有人
    print("Testing Text & @all...")
    text_content = "这是一条普通文本测试消息，注意查收！"
    # mentioned_mobile_list=["@all"] 会通知群里所有人
    notifier.send_text(text_content, mentioned_mobile_list=["@all"])

    print("🏁 测试结束，请查看企业微信群是否收到消息。")


if __name__ == "__main__":
    test_push()