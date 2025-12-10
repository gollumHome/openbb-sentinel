# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 基础配置
    WECHAT_WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL")
    FMP_KEY = os.getenv("FMP_API_KEY")
    TIINGO_KEY = os.getenv("TIINGO_API_KEY")
    WATCHLIST = ["NVDA","AAPL", "MSFT", "GOOG", "AMZN", "META","TSLA","PLTR","MSTR"]

    # 1. RSI (相对强弱指数) 阈值
    # RSI 范围是 0-100。
    RSI_OVERBOUGHT = 70  # 【超买线】: 当 RSI > 70，说明短期买盘太强，价格可能"虚高"，随时可能回调（卖出/风险信号）。
    RSI_OVERSOLD = 30  # 【超卖线】: 当 RSI < 30，说明短期恐慌抛售过度，价格可能"被低估"，随时可能反弹（买入/机会信号）。

    # 2. ATR (平均真实波幅) 倍数
    # 用于计算"动态止损位" (Trailing Stop)。
    # 公式通常是：止损价 = 现价 - (ATR数值 * 倍数)
    ATR_MULTIPLIER = 1.5  # 【止损宽容度】:
    # 设为 1.5 代表允许价格波动 1.5 倍的日平均波幅。
    # 如果设得太小(如 1.0)，容易被正常波动"震下车"；
    # 如果设得太大(如 3.0)，止损太慢，亏损会变大。

    # Google Gemini 配置
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # 推荐使用 gemini-1.5-flash，速度快且免费额度高
    GEMINI_MODEL = "gemini-1.5-flash"

    # 3. 🔥 关键：判断是否在 GitHub Actions 环境运行
    # GitHub 运行时会自动设置这个变量为 "true"
    IS_GITHUB = os.getenv("GITHUB_ACTIONS") == "true"

    # 4. 本地代理地址 (你的梯子端口)
    # 只有在本地运行时才会被调用
    LOCAL_PROXY = "http://127.0.0.1:10809"
