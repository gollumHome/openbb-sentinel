import os
import google.generativeai as genai

# 1. 填入从 https://aistudio.google.com 申请的新 Key
os.environ["GOOGLE_API_KEY"] = ""

# 2. 填入你的代理 (确保不是香港节点)
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"  # <--- 注意端口号
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"

# 3. 强制 REST 协议
genai.configure(api_key=os.environ["GOOGLE_API_KEY"], transport="rest")

print(f"当前使用的 Key 前缀: {os.environ['GOOGLE_API_KEY'][:5]}...")
print("正在尝试列出模型...")

try:
    # 不猜名字，直接让它列出允许的模型
    models = list(genai.list_models())
    print("✅ 连接成功！可用模型如下：")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - {m.name}")

    # 如果能列出，尝试调用一次
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say Hello")
    print(f"✅ 对话测试成功: {response.text}")

except Exception as e:
    print(f"❌ 依然失败: {e}")
