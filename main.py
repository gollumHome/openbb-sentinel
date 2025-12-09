import argparse
import sys
from datetime import datetime
from openbb import obb

# 导入自定义模块
from config import Config
from data_engine import DataEngine
from ai_brain import AIBrain
from notifier import WeChatNotifier  # <--- ✅ 替换为企业微信


def setup_credentials():
    """统一配置所有数据源凭证"""
    providers_dict = {}

    # 1. 配置 FMP (如果有)
    if hasattr(Config, 'FMP_KEY') and Config.FMP_KEY:
        providers_dict["fmp"] = Config.FMP_KEY

    # 2. 配置 Tiingo (如果有)
    if hasattr(Config, 'TIINGO_KEY') and Config.TIINGO_KEY:
        providers_dict["tiingo"] = Config.TIINGO_KEY

    # 3. 统一登录 OpenBB
    if providers_dict:
        print(f"🔐 正在激活数据源: {list(providers_dict.keys())}")
        try:
            obb.account.login(providers=providers_dict)
        except Exception as e:
            print(f"⚠️ 登录数据源失败 (不影响 yfinance 使用): {e}")
    else:
        print("⚠️ 未检测到 API Key，系统将主要使用 Yahoo Finance 免费数据。")


def format_wechat_message(ticker, mode, insight):
    """
    将 AI 的回复包装成企业微信漂亮的 Markdown 格式
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    if mode == "pre":
        title = f"☀️ 盘前策略: {ticker}"
        # 企业微信支持的颜色: info(绿), warning(橙), comment(灰)
        color_tag = "info"
    else:
        title = f"🌙 复盘总结: {ticker}"
        color_tag = "warning"

    # 构造 Markdown
    # <font color="info">...</font> 是企业微信特有的语法
    msg = f"""
# {title}
<font color="comment">{current_time}</font>

{insight}

---
> 🤖 来自 OpenBB-Sentinel 量化系统
    """
    return msg


def main():
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="OpenBB Sentinel 自动化分析系统")
    parser.add_argument("mode", choices=["pre", "post"], help="pre: 盘前策略, post: 盘后复盘")
    args = parser.parse_args()

    print(f"\n🚀 初始化系统 | 模式: [{args.mode}]")
    print("-" * 50)

    # 2. 初始化环境
    setup_credentials()

    # 3. 实例化模块
    engine = DataEngine()
    brain = AIBrain()
    notifier = WeChatNotifier()  # 读取 Config 中的 Webhook

    # 4. 遍历股票池
    if not Config.WATCHLIST:
        print("⚠️ 警告: Config.WATCHLIST 为空，请先添加关注的股票代码。")
        return

    for ticker in Config.WATCHLIST:
        print(f"\n🔍 正在处理: {ticker} ...")

        try:
            # Step A: 获取数据
            data = engine.get_full_context(ticker)

            # 如果数据获取失败（比如停牌或代码错误），跳过
            if not data:
                print(f"❌ 跳过 {ticker}: 数据获取不完整")
                continue

            # Step B: AI 分析
            # 这里调用我们在 ai_brain.py 里写好的 analyze
            insight = brain.analyze(data, mode=args.mode)

            # Step C: 推送消息
            # 组装 Markdown
            markdown_msg = format_wechat_message(ticker, args.mode, insight)

            # 发送
            print(f"📨 正在推送 {ticker} 分析报告...")
            notifier.send_markdown(markdown_msg)

        except Exception as e:
            print(f"💥 处理 {ticker} 时发生意外错误: {e}")
            # 继续处理下一个股票，不要因为一个报错就停止整个脚本
            continue

    print("-" * 50)
    print("🏁 所有任务执行完毕。")


if __name__ == "__main__":
    main()