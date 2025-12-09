# tests/test_data.py
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_engine import DataEngine


def test_data_fetching():
    symbol = "TSLA"  # 用一个流动性好的股票测试
    print(f"🌍 [测试] 正在尝试从 OpenBB 获取 {symbol} 数据...")
    print("    (这一步取决于网速和 API 限制，请耐心等待...)")

    engine = DataEngine()
    data = engine.get_full_context(symbol)

    if data:
        print("\n✅ 数据获取成功！结构如下：")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 简单断言检查
        if data['quote']['price'] > 0:
            print("\n✅ 价格数据正常")
        else:
            print("\n❌ 价格数据异常")

        if data['technicals']['rsi'] > 0:
            print("✅ 技术指标 (RSI) 计算正常")
        else:
            print("❌ 技术指标计算失败 (可能是 yfinance 网络问题)")
    else:
        print("\n❌ 数据获取失败，返回为 None。请检查 FMP Key 或网络。")


if __name__ == "__main__":
    test_data_fetching()