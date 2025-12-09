# tests/test_config.py
import sys
import os

# 将父目录加入路径，以便能导入 config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def test_config():
    print("📋 [测试] 正在检查配置变量...")

    # 检查各个 Key 是否存在
    checks = [
        ("GOOGLE_API_KEY", Config.GOOGLE_API_KEY),
        ("FMP_KEY", Config.FMP_KEY),
        ("FEISHU_WEBHOOK", Config.FEISHU_WEBHOOK)
    ]

    all_pass = True
    for name, value in checks:
        if value and len(value) > 5:
            # 只显示后4位，保护隐私
            masked = "..." + value[-4:]
            print(f"✅ {name}: 已加载 ({masked})")
        else:
            print(f"❌ {name}: 未加载或格式错误！")
            all_pass = False

    if all_pass:
        print("\n🎉 配置模块测试通过！")
    else:
        print("\n⚠️ 配置测试失败，请检查 .env 文件。")


if __name__ == "__main__":
    test_config()