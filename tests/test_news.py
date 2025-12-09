import yfinance as yf
import requests
import json
import xml.etree.ElementTree as ET
import urllib3

# 关闭 SSL 警告
urllib3.disable_warnings()

# ----------------------------------------------------

PROXY_URL = "http://127.0.0.1:10809"
# ----------------------------------------------------

SYMBOL = "TSLA"  # 测试代码


def test_method_1_yfinance():
    """方法1: 使用 yfinance 官方接口 (最推荐)"""
    print(f"\n🧪 [测试 1] 正在尝试 yfinance 库...")

    try:
        # 强制更新库的提醒
        import yfinance
        print(f"    (当前 yfinance 版本: {yfinance.__version__}) -> 建议 >= 0.2.40")

        tk = yf.Ticker(SYMBOL)

        # 获取新闻
        news = tk.news

        if not news:
            print("    ❌ yfinance 返回的新闻列表为空 []。")
            print("    👉 建议运行: pip install --upgrade yfinance")
            return

        print(f"    ✅ yfinance 获取成功! 共有 {len(news)} 条:")
        for i, item in enumerate(news[:2]):
            # 打印原始结构，方便调试
            print(f"      [{i}] 标题: {item.get('title')}")
            print(f"           时间: {item.get('providerPublishTime')}")

    except Exception as e:
        print(f"    ❌ yfinance 报错: {e}")


def test_method_2_rss_direct():
    """方法2: 暴力请求 Yahoo RSS (绕过 SSL 验证)"""
    print(f"\n🧪 [测试 2] 正在尝试 Yahoo RSS 直连 (忽略 SSL)...")

    url = f"https://finance.yahoo.com/rss/headline?s={SYMBOL}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL
    } if PROXY_URL else None

    try:
        # verify=False 解决 'handshake operation timed out'
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=10, verify=False)

        print(f"    📡 状态码: {resp.status_code}")

        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall('./channel/item')
            print(f"    ✅ RSS 获取成功! 共有 {len(items)} 条:")

            for i, item in enumerate(items[:2]):
                title = item.find('title').text
                print(f"      [{i}] {title}")
        else:
            print("    ❌ RSS 请求被拒绝 (非200)")

    except Exception as e:
        print(f"    ❌ RSS 请求报错: {e}")


def test_method_3_google_news():
    """方法3: 备用方案 - Google News RSS"""
    print(f"\n🧪 [测试 3] 正在尝试 Google News RSS (备用)...")

    # Google News 针对特定股票的搜索
    url = f"https://news.google.com/rss/search?q={SYMBOL}+stock&hl=en-US&gl=US&ceid=US:en"

    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL
    } if PROXY_URL else None

    try:
        resp = requests.get(url, proxies=proxies, timeout=10, verify=False)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall('./channel/item')
            print(f"    ✅ Google News 获取成功! 共有 {len(items)} 条:")
            for i, item in enumerate(items[:2]):
                title = item.find('title').text
                print(f"      [{i}] {title}")
        else:
            print("    ❌ Google News 请求失败")

    except Exception as e:
        print(f"    ❌ Google News 报错: {e}")


if __name__ == "__main__":
    print(f"🔥 开始诊断新闻获取模块 (目标: {SYMBOL})")
    test_method_1_yfinance()
    test_method_2_rss_direct()
    test_method_3_google_news()