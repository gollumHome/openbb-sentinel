# ai_brain.py
from asyncio import exceptions

import google.generativeai as genai
from google.api_core import exceptions
from config import Config
import os


if not Config.IS_GITHUB:
    os.environ["HTTP_PROXY"] = Config.LOCAL_PROXY
    os.environ["HTTPS_PROXY"] = Config.LOCAL_PROXY
    print(f"🌍 [本地模式] 已开启 Gemini 代理: {Config.LOCAL_PROXY}")
else:
    print("☁️ [GitHub 模式] 直连 Google，不使用代理")

from google.generativeai.types import HarmCategory, HarmBlockThreshold




class AIBrain:
    def __init__(self):
        # 1. 配置 Gemini
        if not Config.GOOGLE_API_KEY:
            raise ValueError("请在 .env 中配置 GOOGLE_API_KEY")
        genai.configure(api_key=Config.GOOGLE_API_KEY, transport="rest")
        # 2. 初始化模型配置
        # generation_config 可以控制回复的随机性，temperature 越低越严谨
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 5120,
        }

        self.model_name = Config.GEMINI_MODEL

    def analyze(self, data, mode="pre"):
        """
        全量数据投喂版
        """
        mode_name = "☀️ 盘前策略" if mode == "pre" else "🌙 盘后复盘"
        print(f"🧠 [Gemini] 正在生成 {data['symbol']} {mode_name}...")

        # --- 1. 数据提取  ---
        # 宏观
        macro = data.get('macro', {})
        spy_chg = macro.get('spy_change', 0.0)
        qqq_chg = macro.get('qqq_change', 0.0)

        # 期权
        opt = data.get('options', {})
        pcr = opt.get('pcr', 'N/A')
        pressure = opt.get('pressure', 'N/A')

        # 止损
        stop_loss = round(data['quote']['price'] - Config.ATR_MULTIPLIER * data['technicals']['atr'], 2)

        # 新闻与基本面 (之前漏掉的！)
        news_text = data.get('news', '暂无重大新闻')
        target_price = data.get('fundamental', 'N/A')

        # --- 2. 构建全量上下文 (Full Context) ---
        context_str = f"""
            [基础信息]
            标的: {data['symbol']}
            现价: ${data['quote']['price']} (涨跌幅 {data['quote']['change_pct']}%)
    
            [大盘环境]
            🇺🇸 SPY (标普): {spy_chg}%
            💻 QQQ (纳指): {qqq_chg}%
    
            [消息面 & 基本面] 🔥
            最新新闻: {news_text}
            机构目标价: ${target_price}
    
            [技术指标]
            SMA20: ${data['technicals']['sma20']}
            RSI(14): {data['technicals']['rsi']}
            ATR(波动): {data['technicals']['atr']}
    
            [期权筹码]
            PCR: {pcr}
            压力位: ${pressure}
    
            [风控参考]
            建议止损: < ${stop_loss}
        """

        print("-" * 40)
        print(f"📊 投喂数据预览 (含新闻):\n{context_str.strip()}")
        print("-" * 40)

        # --- 3. Prompt 升级 (强制分析新闻) ---

        if mode == "pre":
            # === ☀️ 盘前模式 ===
            system_instruction = """
            你是一位擅长"消息驱动"的华尔街交易员。
            分析核心：必须将【最新新闻】作为第一分析要素。如果新闻是重大利好/利空，可以适当忽略技术指标。
            """

            user_prompt = f"""
            请基于上述数据，制定【盘前交易计划】。

            请严格按以下结构输出（中文）：

            1. 📰 **消息面解读** (最重要)：
               - {news_text}
               - 这条新闻对股价是直接利好、利空，还是噪音？(如果无新闻，请注明"无催化剂，跟随大盘")

            2. 🌍 **宏观与情绪**：
               - QQQ/SPY 的表现是否支持今日做多？
               - RSI 和 PCR 是否暗示情绪过热？

            3. 🎯 **关键博弈点**：
               - 上方压力位 ${pressure} 是否难以突破？
               - 下方支撑位看哪里？

            4. 🚀 **操作策略**：
               - 给出一个具体的开盘操作思路。

            (数据如下：\n{context_str})
            """

        else:
            system_instruction = """
                        你是一位拥有20年经验的"基金经理"和风控专家。你的核心能力是进行【收盘归因】和【隔夜风险评估】。
                        你的风格：冷静、客观、数据导向。你非常关注股价是否偏离了基本面或宏观大势。
                        分析重点：今天的涨跌是消息驱动还是情绪驱动？收盘价是否破坏了关键逻辑？明天怎么做？
                        """
            user_prompt = f"""
                        请基于今天的收盘数据，撰写一份深度的【盘后复盘报告】。

                        请严格按以下结构输出（中文）：

                        1. 🔍 **复盘归因 (最重要的部分)**：
                           - **新闻验证**：今日的走势是否与新闻 ({news_text}) 相符？是利好兑现还是利空出尽？
                           - **强弱对比**：个股涨跌幅 vs 科技指数(QQQ) vs 大盘(SPY)。如果是缩量上涨或背离大盘下跌，请重点示警。

                        2. ⚖️ **趋势与形态**：
                           - **生命线检查**：收盘价相对于 SMA20 的位置。如果跌破，是假摔还是有效破位？
                           - **动能诊断**：RSI 是否处于过热(>70)或超卖(<30)区域？

                        3. ⚠️ **持仓体检 (风控核心)**：
                           - **期权筹码**：PCR ({pcr}) 显示主力情绪如何？上方压力位 ${pressure} 距离现价还有多远？
                           - **估值参考**：现价距离机构目标价 ${target_price} 是还有空间，还是已经透支？
                           - **隔夜风险评级**：(高 / 中 / 低) —— 请给出理由。

                        4. 🔮 **明日剧本**：
                           - 如果明日低开，必须坚决离场的**防守价**是多少？
                           - 如果明日高开，关注哪个**阻力位**的突破情况？

                        (完整数据如下：\n{context_str})
                        """
        # --- 4. 安全设置与调用 (保持不变) ---
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # --- ✨ 5. 核心修改：增加重试机制 ---
        max_retries = 3  # 最大重试次数
        retry_delay = 30  # 每次等待秒数 (针对 Pro 模型建议设为 30s 以上)

        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config,
                    system_instruction=system_instruction
                )

                # 发送请求
                response = model.generate_content(user_prompt, safety_settings=safety_settings)

                if response.candidates and response.candidates[0].content.parts:
                    final_text = response.text
                    if response.candidates[0].finish_reason.name == "MAX_TOKENS":
                        final_text += "\n[⚠️ 截断]"
                    return final_text
                else:
                    return "AI 未生成有效内容 (内容为空)"

            except exceptions.ResourceExhausted:
                # 🛑 专门捕捉 429 限流错误
                print(
                    f"⏳ [限流警告] 触发 Gemini 速率限制，正在休眠 {retry_delay} 秒后重试 ({attempt + 1}/{max_retries})...")
                import time
                time.sleep(retry_delay)  # 强制休息

            except Exception as e:
                # 其他错误（如网络断开、参数错误）
                print(f"❌ Gemini 调用报错: {e}")
                return f"AI 服务不可用: {str(e)}"

        return "❌ 超过最大重试次数，分析失败"