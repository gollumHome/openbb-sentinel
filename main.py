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

    MAX_LENGTH = 1800  # 企业微信限制约2048字节，留点余量给标题
    current_batch = []
    current_length = 0
    batch_counter = 1

    separator = "\n" + "·" * 30 + "\n"

    for insight in all_insights:
        # 估算加入这条消息后的总长度
        # 注意：这里简单按字符数计算，如果包含大量中文，建议设低一点（如 600-800）
        insight_len = len(insight.encode('utf-8'))  # 计算字节长度更准确

        # 如果当前缓存 + 新消息 + 分隔符 超过限制，则先发送当前缓存
        if current_length + insight_len > MAX_LENGTH and current_batch:
            # 发送当前批次
            msg_body = separator.join(current_batch)
            full_msg = f"【{args.mode.upper()} 汇总 ({batch_counter})】\n{msg_body}"
            notifier.send(full_msg)
            print(f"📤 第 {batch_counter} 批已发送 (长度: {current_length})")

            # 重置
            current_batch = []
            current_length = 0
            batch_counter += 1
            time.sleep(2)

        # 加入新消息到缓存
        current_batch.append(insight)
        current_length += insight_len + len(separator.encode('utf-8'))

    # 发送剩余的最后一批
    if current_batch:
        msg_body = separator.join(current_batch)
        full_msg = f"【{args.mode.upper()} 汇总 ({batch_counter}) - 完】\n{msg_body}"
        notifier.send(full_msg)
        print(f"📤 最后一批已发送。")

    print("-" * 50)
    print("🏁 所有任务执行完毕。")


if __name__ == "__main__":
    main()