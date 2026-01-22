import argparse
from openbb import obb


from config import Config
from data_engine import DataEngine
from ai_brain import AIBrain
from notifier import WeChatNotifier
from datetime import datetime
import pytz
import time

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
    # --- 2. 这里修改为北京时间 ---
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    # ---------------------------

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
<font color="comment">{current_time} (北京时间)</font>

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
    notifier = WeChatNotifier()

    # 4. 遍历股票池
    if not Config.WATCHLIST:
        print("⚠️ 警告: Config.WATCHLIST 为空。")
        return

    all_insights = []  # 用于存储所有股票的分析结果

    for ticker in Config.WATCHLIST:
        print(f"\n🔍 正在处理: {ticker} ...")
        try:
            # Step A: 获取数据
            data = engine.get_full_context(ticker)
            if not data:
                continue

            # Step B: AI 分析
            insight = brain.analyze(data, mode=args.mode)

            # Step C: 格式化单条消息并存入列表
            # 注意：这里只负责生成单个标的文本，不直接发送
            formatted_insight = format_wechat_message(ticker, args.mode, insight)
            all_insights.append(formatted_insight)

            print(f"✅ {ticker} 分析完成并已暂存。")

            # 为了规避 Gemini/数据源 频率限制，依然保留 sleep，但不在此时发消息
            if ticker != Config.WATCHLIST[-1]:  # 最后一个标的后不需要等
                print(f"☕ 休息 60 秒避免 API 限流...")
                time.sleep(60)

        except Exception as e:
            print(f"💥 处理 {ticker} 时发生意外错误: {e}")
            continue

    # 5. 分批汇总推送
    if not all_insights:
        print("望天... 没有生成任何有效分析。")
        return

    print(f"\n📨 正在合并推送 {len(all_insights)} 个标的的分析报告...")

    # 设定每批发送的数量（建议 3 个标的一发，防止内容过长被微信截断）
    batch_size = 3
    for i in range(0, len(all_insights), batch_size):
        batch = all_insights[i: i + batch_size]

        # 合并文本，中间加个分割线
        separator = "\n" + "·" * 30 + "\n"
        combined_message = f"【{args.mode.upper()} 汇总报告 ({i // batch_size + 1})】\n"
        combined_message += separator.join(batch)

        # 发送
        notifier.send(combined_message)  # 推荐用 markdown 格式更美观
        print(f"📤 第 {i // batch_size + 1} 批报告已推送。")

        # 短暂休眠防止微信 Webhook 限流（通常 Webhook 也有 20条/分 的限制）
        time.sleep(2)

    print("-" * 50)
    print("🏁 所有任务执行完毕。")


if __name__ == "__main__":
    main()