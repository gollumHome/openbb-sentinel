import yfinance as yf
import requests

# 你的端口
PROXY_URL = "http://127.0.0.1:10809"

print(f"1. 测试 requests 连通性 (代理: {PROXY_URL})...")
try:
    # 先测能不能访问 Google，验证代理本身是通的
    resp = requests.get("https://www.google.com", proxies={"http": PROXY_URL, "https": PROXY_URL}, timeout=5)
    print(f"✅ 代理连通成功！状态码: {resp.status_code}")
except Exception as e:
    print(f"❌ 代理连不通！请检查你的梯子软件是否开启，端口是不是写错了？\n错误: {e}")
    exit()

print("\n2. 测试 yfinance 下载...")
try:
    # 显式配置 yfinance
    yf.set_config(proxy=PROXY_URL)

    # 下载数据
    df = yf.download("TSLA", period="1d", progress=False)

    if not df.empty:
        print("✅ yfinance 下载成功！")
        print(df)
    else:
        print("❌ yfinance 返回为空 (但没报错)。")
except Exception as e:
    print(f"❌ yfinance 报错: {e}")