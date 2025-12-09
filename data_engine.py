import os
import sys
import warnings
import pandas as pd
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
from openbb import obb

from config import Config

if not Config.IS_GITHUB:
    os.environ["HTTP_PROXY"] = Config.LOCAL_PROXY
    os.environ["HTTPS_PROXY"] = Config.LOCAL_PROXY
    print(f"🌍 [本地模式] 已开启 Gemini 代理: {Config.LOCAL_PROXY}")
else:
    PROXY_URL = None
    print("☁️ [GitHub 模式] 直连 Google，不使用代理")

PROXY_URL = os.environ["HTTP_PROXY"]
# 屏蔽警告
warnings.filterwarnings("ignore")


class DataEngine:

    def __init__(self):
        # 🟢 修复：初始化时加载 FMP Key，否则新闻拿不到
        if Config.FMP_KEY:
            try:
                obb.user.credentials.fmp_api_key = Config.FMP_KEY
                print(f"    [System] FMP Key 已加载")
            except Exception as e:
                print(f"    [System] FMP 登录失败: {e}")


    def get_full_context(self, symbol):
        print(f"🔄 [Data] 正在扫描 {symbol}...")

        # 1. 🔥 调用新的宏观获取方法
        macro_data = self._get_market_indices()

        # ==================================================
        # 🚀 第一步：获取历史数据 (核心资产)
        # ==================================================
        # 我们一次性下载 1 年的数据，既包含了“当前价格”，也包含了“技术分析素材”
        hist_df = self._fetch_history_direct(symbol)

        if hist_df is None or hist_df.empty:
            print(f"❌ {symbol} 数据获取完全失败，跳过。")
            return None

        # ==================================================
        # 🚀 第二步：拆解数据
        # ==================================================

        # 1. 从历史数据中提取【当前报价】
        quote_data = self._extract_quote(hist_df)

        # 2. 使用历史数据计算【技术指标】
        # (因为 hist_df 已经在本地了，这一步不需要联网，极快！)
        tech_data = self._calculate_technicals(hist_df)

        # 3. 获取新闻 (这个还要连一次网，走 FMP)
        news_data = self._get_news(symbol)

        # 4. 获取期权 PCR (YF 直连)
        options_data = self._get_options_direct(symbol)

        # 5. 获取机构目标价 (YF 直连 - 替代 FMP)
        fund_data = self._get_fundamental_direct(symbol)

        # 4. 组装返回
        return {
            "symbol": symbol,
            "quote": quote_data,
            "technicals": tech_data,
            "news": news_data,
            "options": options_data,
            "fundamental": fund_data,
            "macro": {
                "spy_change": macro_data["SPY"],
                "qqq_change": macro_data["QQQ"]
            }
        }

    def _fetch_history_direct(self, symbol):
        """
        直连 YFinance 下载历史数据，并清洗成 OpenBB 喜欢的格式
        """
        print(f"    [1] 直连 YFinance 下载 {symbol} 历史 K 线...")
        try:
            # 下载最近 1 年数据 (足够算 200日均线了)
            df = yf.download(symbol, period="1y", progress=False, proxy=PROXY_URL, timeout=30)

            if df.empty:
                print("    ❌ YFinance 返回空数据")
                return None

            # --- 数据清洗 (关键步骤) ---
            # 1. 处理 MultiIndex (yfinance 新版特性)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 2. 重命名列 (OpenBB 强制要求列名必须是小写: open, high, low, close, volume)
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume", "Adj Close": "adj_close"
            })

            # 3. 确保索引是 Datetime 类型
            df.index = pd.to_datetime(df.index)

            return df

        except Exception as e:
            print(f"    ❌ 下载报错: {e}")
            return None

    def _extract_quote(self, df):
        """从 K 线表中提取最新价格"""
        try:
            price = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            change = (price - prev_close) / prev_close * 100

            print(f"    ✅ 报价提取成功: {price:.2f}")
            return {
                "price": round(float(price), 2),
                "change_pct": round(float(change), 2),
                "source": "YFinance"
            }
        except:
            return None

    def _calculate_technicals(self, df):
        """将清洗好的 DF 喂给 OpenBB 计算技术指标"""
        print("    [2] 正在计算技术指标 (RSI, ATR, MA)...")
        # 默认返回值
        defaults = {"rsi": 50.0, "atr": 0.0, "sma20": 0.0}

        # 0. 基础检查
        if df is None or df.empty:
            print("    ⚠️ 数据为空，跳过计算")
            return defaults
        try:
            # 确保数据按时间升序 (OpenBB 依赖时间序列)
            # 假设索引是日期，如果日期在列里，请先 set_index
            df = df.sort_index(ascending=True)
            #指定 provider='pandas-ta' 确保在本地快速计算，不依赖外部 API
            provider = "pandas-ta"

            # 1. RSI (14)
            rsi_res = obb.technical.rsi(data=df,target="close", window=14,provider=provider).to_df()
            # 智能查找：找列名里包含 'rsi' 的那一列
            rsi_col = [c for c in rsi_res.columns if 'rsi' in str(c).lower()]
            rsi = rsi_res[rsi_col[0]].iloc[-1] if rsi_col else 50.0

            # 2. ATR (14)
            atr_res = obb.technical.atr(data=df, high="high", low="low", close="close", window=14).to_df()
            # 智能查找：找列名里包含 'atr' 的那一列 (排除 'ATRr_14' 这种变体)
            atr_col = [c for c in atr_res.columns if 'atr' in str(c).lower()]
            atr = atr_res[atr_col[0]].iloc[-1] if atr_col else 0.0

            # 3. SMA (20)
            sma_res = obb.technical.sma(data=df, target="close", window=20).to_df()
            # 智能查找：找列名里包含 'sma' 的那一列
            sma_col = [c for c in sma_res.columns if 'sma' in str(c).lower()]
            sma20 = sma_res[sma_col[0]].iloc[-1] if sma_col else 0.0

            return {
                "rsi": round(float(rsi), 2),
                "atr": round(float(atr), 2),
                "sma20": round(float(sma20), 2)
            }
        except Exception as e:
            print(f"    ⚠️ 指标计算失败: {e}")
            # 打印一下出错时的列名，方便调试
            # print(f"DEBUG: RSI Cols: {rsi_res.columns if 'rsi_res' in locals() else 'N/A'}")
            return {"rsi": 50.0, "atr": 0.0, "sma20": 0.0}

    def _get_news(self, symbol):
        """
        获取新闻 (双保险策略: Yahoo RSS -> Google News RSS)
        """
        print(f"    [4] 正在获取 {symbol} 新闻...")
        import requests
        import xml.etree.ElementTree as ET
        import urllib3

        proxies = None
        if not Config.IS_GITHUB:
            proxies = {
                "http": Config.LOCAL_PROXY,
                "https": Config.LOCAL_PROXY
            }

        # 🤫 关闭 SSL 证书验证警告 (控制台看起来清爽点)
        urllib3.disable_warnings()

        # 伪装成浏览器 (防反爬关键)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # --- 策略 A: Yahoo Finance RSS (首选) ---
        try:
            rss_url = f"https://finance.yahoo.com/rss/headline?s={symbol}"

            resp = requests.get(rss_url, headers=headers, timeout=10, verify=False, proxies=proxies)

            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                news_text = ""
                count = 0

                # 遍历 XML
                for item in root.findall('./channel/item'):
                    if count >= 3: break  # 只取前3条，给AI省空间

                    title = item.find('title').text
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""

                    # 格式化时间 (去掉后面多余的时区信息)
                    # 原格式: Tue, 09 Dec 2025 10:30:00 GMT
                    short_date = pub_date[:16] if len(pub_date) > 16 else "近期"

                    news_text += f"- {title} [{short_date}]\n"
                    count += 1

                if news_text:
                    return news_text.strip()

        except Exception as e:
            print(f"    ⚠️ Yahoo RSS 获取失败: {e}，尝试切换备用源...")

        # --- 策略 B: Google News RSS (备胎) ---
        try:
            print("    🔄 切换至 Google News 源...")
            # 针对股票的搜索查询
            g_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"

            resp = requests.get(g_url, headers=headers, timeout=10, verify=False)

            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                news_text = ""
                count = 0

                for item in root.findall('./channel/item'):
                    if count >= 3: break

                    title = item.find('title').text
                    # Google 的 pubDate 也很长，同样截取
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    short_date = pub_date[:16] if len(pub_date) > 16 else "近期"

                    news_text += f"- {title} [{short_date}]\n"
                    count += 1

                if news_text:
                    return news_text.strip()

        except Exception as e:
            print(f"    ❌ Google News 也失败: {e}")

        return "暂无重大新闻 (接口未返回数据)"

    # 通过 Yahoo 获取期权 PCR
    def _get_options_direct(self, symbol):
        print("    [3] 计算期权 PCR (YFinance)...")
        try:
            tk = yf.Ticker(symbol)
            # 获取最近的一个期权日期
            if not tk.options:
                return {"pcr": "N/A", "pressure": "N/A"}

            date = tk.options[0]  # 最近到期日
            opts = tk.option_chain(date)

            # 计算 PCR (Volume)
            puts_vol = opts.puts['volume'].sum()
            calls_vol = opts.calls['volume'].sum()
            pcr = round(puts_vol / calls_vol, 2) if calls_vol > 0 else 1.0

            # 计算压力位 (Call Open Interest 最大的行权价)
            max_call_row = opts.calls.loc[opts.calls['openInterest'].idxmax()]
            pressure = max_call_row['strike']

            return {"pcr": pcr, "pressure": pressure}
        except Exception as e:
            # print(f"期权错误: {e}")
            return {"pcr": "N/A", "pressure": "N/A"}

     # 通过 Yahoo 获取机构目标价
    def _get_fundamental_direct(self, symbol):
        try:
            tk = yf.Ticker(symbol)
            # Yahoo 的 info 接口包含了 targetMeanPrice
            # 注意：info 接口可能会慢，且通过代理访问
            target = tk.info.get('targetMeanPrice', 'N/A')
            return target
        except:
            return "N/A"

    def _get_market_indices(self):
        """
        [原生 yfinance 版] 同时获取 SPY (标普) 和 QQQ (纳指) 的涨跌幅
        使用 fast_info 接口，速度极快且稳定
        """
        print("    [0] 正在获取大盘 (SPY & QQQ)...")

        # 必须在文件顶部 import yfinance as yf
        # 如果 DataEngine 类里没引，记得加上： import yfinance as yf
        import yfinance as yf

        indices = {
            "SPY": 0.0,
            "QQQ": 0.0
        }

        try:
            # 1. 初始化 Tickers 对象
            tickers = yf.Tickers("SPY QQQ")

            # 2. 遍历获取
            for symbol in ["SPY", "QQQ"]:
                try:
                    # 获取单个 ticker 对象
                    t = tickers.tickers[symbol]

                    # 🔥 使用 fast_info (这是获取实时价格最快的方法)
                    # 它不需要像 .info 那样去爬取完整的元数据，几乎是瞬间返回
                    last_price = t.fast_info['last_price']
                    prev_close = t.fast_info['previous_close']

                    if prev_close and prev_close > 0:
                        # 手动计算涨跌幅: (当前价 - 昨收价) / 昨收价 * 100
                        change_pct = ((last_price - prev_close) / prev_close) * 100
                        indices[symbol] = round(change_pct, 2)
                    else:
                        print(f"    ⚠️ {symbol} 昨收价异常")
                        indices[symbol] = 0.0

                except Exception as inner_e:
                    print(f"    ⚠️ 获取 {symbol} 详情失败: {inner_e}")
                    indices[symbol] = 0.0

        except Exception as e:
            print(f"    ⚠️ 大盘数据获取严重失败: {e}")
            # 保持默认值 0.0

        return indices