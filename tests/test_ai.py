# tests/test_ai.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_brain import AIBrain
from tests.mock_data import MOCK_CONTEXT


def test_gemini_connection():
    print("🧠 [测试] 正在连接 Google Gemini...")

    try:
        brain = AIBrain()

        # 简单测试一个 Hello World 级别的对话，确保连通性
        print("    正在发送测试请求...")
        insight = brain.analyze(MOCK_CONTEXT, mode="pre")

        print("\n--- Gemini 回复 ---")
        print(insight)
        print("-------------------\n")

        if len(insight) > 10:
            print("✅ Gemini 连接成功且响应正常！")
        else:
            print("⚠️ Gemini 响应内容为空。")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("提示：请检查 .env 里的 GOOGLE_API_KEY 是否正确，以及是否有 Google AI Studio 的访问权限（需科学上网）。")


if __name__ == "__main__":
    test_gemini_connection()