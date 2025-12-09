# tests/mock_data.py
# 这是一个模拟 DataEngine 返回的数据结构，用于测试 AI 和 推送
MOCK_CONTEXT = {
    "symbol": "TEST-TICKER",
    "quote": {
        "price": 888.88,
        "change_pct": 2.5,  # 涨 2.5%
        "volume": 1000000
    },
    "macro": {
        "spy_change": -0.5  # 大盘跌
    },
    "technicals": {
        "rsi": 75,         # 超买
        "atr": 10.0,
        "sma20": 800.0
    },
    "options": {
        "pcr": 0.6,        # 看涨情绪强
        "pressure": 900
    },
    "news": "1. 该公司刚刚发布了划时代的 AI 产品。\n2. CEO 宣布回购股票。",
    "fundamental": 950.0   # 机构目标价
}