import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import time
import random

# ================= 0. 突破封鎖的連線設定 =================
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'
]
safe_session = requests.Session()
safe_session.headers.update({'User-Agent': random.choice(user_agents)})

# ================= 1. 網頁與 CSS 配置 =================
st.set_page_config(page_title="台股動態觀測站", layout="wide")

st.markdown("""
<style>
    .summary-card { background-color: #f8f9fa; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .metric-card { background-color: #ffffff; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border: 1px solid #edf2f7; }
    .tag-pill { background-color: #e2e8f0; color: #4a5568; padding: 5px 12px; border-radius: 20px; font-size: 14px; margin-right: 8px; display: inline-block; }
    .grid-btn { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; text-align: center; font-weight: bold; color: #2d3748; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

if 'custom_themes' not in st.session_state:
    st.session_state['custom_themes'] = {}

# ================= 2. 核心資料庫 =================
BASE_STOCK_DB = {
    "AI伺服器": {"2330.TW": "台積電", "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "2376.TW": "技嘉", "6669.TW": "緯穎", "3706.TW": "神達", "2356.TW": "英業達"},
    "散熱與水冷": {"3017.TW": "奇鋐", "3324.TWO": "雙鴻", "2421.TW": "建準", "8996.TW": "高力", "3483.TW": "力致", "3653.TW": "健策"},
    "電源與BBU": {"2308.TW": "台達電", "2301.TW": "光寶科", "6409.TW": "旭隼", "6121.TWO": "新普", "6781.TW": "AES-KY", "3211.TWO": "順達"},
    "CoWoS封裝": {"3131.TWO": "弘塑", "6187.TWO": "萬潤", "5443.TW": "均豪", "6640.TWO": "均華", "3583.TW": "辛耘", "6515.TW": "穎崴"},
    "矽光子CPO": {"4979.TWO": "華星光", "3450.TW": "聯鈞", "3081.TWO": "聯亞", "3363.TW": "上詮", "6442.TW": "光聖", "3163.TWO": "波若威"},
    "特化與光阻": {"4770.TW": "上品", "1773.TW": "勝一", "4755.TW": "三福化", "1727.TW": "中華化", "4763.TW": "材料-KY"},
    "面板級封測": {"3711.TW": "日月光投控", "2449.TW": "京元電子", "6257.TW": "矽格", "3481.TW": "群創", "8064.TWO": "東捷"},
    "廠務與無塵室": {"2404.TW": "漢唐", "3402.TWO": "漢科", "6139.TW": "亞翔", "5536.TW": "聖暉*"},
    "IP矽智財": {"3443.TW": "智原", "3661.TW": "世芯-KY", "6643.TWO": "M31", "6533.TW": "晶心科", "3529.TWO": "力旺"},
    "ABF載板": {"3037.TW": "欣興", "8046.TW": "南電", "3189.TW": "景碩"},
    "網通與光通訊": {"3596.TW": "智易", "5388.TW": "中磊", "3380.TW": "明泰", "6285.TW": "啟碁"},
    "低軌衛星": {"2313.TW": "華通", "3491.TWO": "昇達科", "6271.TW": "同欣電", "2485.TW": "兆赫"},
    "機器人與自動化": {"2359.TW": "所羅門", "2365.TW": "昆盈", "6414.TW": "樺漢", "8374.TW": "羅昇", "2049.TW": "上銀"},
    "AI PC": {"2357.TW": "華碩", "2353.TW": "宏碁", "2395.TW": "研華", "8114.TW": "振樺電"},
    "功率元件": {"8255.TWO": "朋程", "3645.TW": "達邁", "5425.TWO": "台半", "8261.TWO": "富鼎", "3317.TWO": "尼克森"} 
}
STOCK_DB = {**BASE_STOCK_DB, **st.session_state['custom_themes']}
SYMBOL_TO_THEME = {sym: theme for theme, stocks in STOCK_DB.items() for sym in stocks}

def get_tw_stock_name(symbol):
    try:
        url = f"https://tw.stock.yahoo.com/quote/{symbol}"
        res = safe_session.get(url, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.find('title').text
        return title.split('(')[0].strip() if title else f"自選_{symbol}"
    except: return f"自選_{symbol}"

# ================= 3. 資料抓取引擎 =================
@st.cache_data(ttl=1800)
def get_market_summary_and_tags():
    try:
        url_tw = "https://news.google.com/rss/search?q=台股+OR+半導體+OR+外資&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        res = safe_session.get(url_tw, timeout=8)
        soup = BeautifulSoup(res.text, 'xml')
        titles = [item.title.text.split(' - ')[0] for item in soup.find_all('item')[:8]]
        
        if titles:
            summary_text = "今日盤面焦點： " + "；".join(titles[:3]) + "。資金輪動快速，建議留意籌碼與均線防守。"
            all_text = "".join(titles)
            keywords = ["台積電", "AI", "外資", "散熱", "鴻海", "聯發科", "降息", "ETF", "營收", "半導體", "漲停"]
            found_tags = [kw for kw in keywords if kw in all_text]
            tags = found_tags[:4] if found_tags else ["盤整", "觀望"]
        else:
            summary_text = "目前市場無重大突發消息，呈現量縮整理格局。"
            tags = ["平穩", "量縮"]
        return summary_text, tags
    except:
        return "新聞擷取保護啟動，暫無最新摘要 (受限於 Google 防護機制)。", ["防護中"]

@st.cache_data(ttl=600)
def get_indices():
    indices_dict = {"加權指數": "^TWII", "台指期近月": "TWF=F", "台積電 ADR": "TSM", "費城半導體": "^SOX"}
    res = {}
    for name, symbol in indices_dict.items():
        try:
            hist = yf.Ticker(symbol, session=safe_session).history(period="5d")
            if len(hist) >= 2:
                close, prev = float(hist['Close'].iloc[-1]), float(hist['Close'].iloc[-2])
                res[name] = {"現價": round(close, 2), "漲跌幅": round((close-prev)/prev*100, 2)}
            else: res[name] = {"現價": 0, "漲跌幅": 0}
        except: res[name] = {"現價": 0, "漲跌幅": 0}
    return res

@st.cache_data(ttl=300)
def fetch_single_stock(symbol):
    try:
        symbol = str(symbol).strip()
        tkr = f"{symbol}.TW"
        hist = yf.Ticker(tkr, session=safe_session).history(period="6mo")
        if hist.empty:
            tkr = f"{symbol}.TWO"
            hist = yf.Ticker(tkr, session=safe_session).history(period="6mo")
        if hist.empty or len(hist) < 20: return None, ""
        name = get_tw_stock_name(symbol)
        display_name = f"🎯 搜尋結果: {name} ({symbol})"
        hist['MA5'], hist['MA20'] = hist['Close'].rolling(5).mean(), hist['Close'].rolling(20).mean()
        return hist, display_name
    except: return None, ""

@st.cache_data(ttl=600)
def get_stock_data_v95(stock_dict):
    data_list, price_history_dict = [], {}
    if not stock_dict: return pd.DataFrame(data_list), price_history_dict

    tickers = list(stock_dict.keys())
    batch_data = {}
    
    # 💡 終極防護：切碎請求，單線程抓取，每次休息1秒鐘，絕對不給 Yahoo 封鎖的機會
    chunk_size = 10
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i + chunk_size]
        try:
            temp_batch = yf.download(chunk, period="6mo", group_by="ticker", progress=False, threads=False, session=safe_session)
            if len(chunk) == 1:
                batch_data[chunk[0]] = temp_batch
            else:
                for t in chunk:
                    if t in temp_batch.columns.get_level_values(0):
                        batch_data[t] = temp_batch[t]
        except: pass
        time.sleep(1) # 讓爬蟲好好休息 1 秒，偽裝成人類

    for full_symbol, name in stock_dict.items():
        try:
            if full_symbol not in batch_data: continue
            hist = batch_data[full_symbol].copy().dropna(subset=['Close', 'Volume', 'Open', 'High', 'Low'])
            if hist.empty: continue
            
            symbol = full_symbol.split('.')[0]
            close, prev_close = float(hist['Close'].iloc[-1]), float(hist['Close'].iloc[-2])
            open_p, high_p, low_p = float(hist['Open'].iloc[-1]), float(hist['High'].iloc[-1]), float(hist['Low'].iloc[-1])
            change_pct = ((close - prev_close) / prev_close) * 100
            
            upper_shadow = high_p - max(open_p, close)
            lower_shadow = min(open_p, close) - low_p
            body = abs(open_p - close)
            
            k_pattern = "-"
            if lower_shadow > body * 1.5 and lower_shadow > upper_shadow:
                k_pattern = "📌 長下影 (探底)"
            elif upper_shadow > body * 1.5 and upper_shadow > lower_shadow:
                k_pattern = "⚠️ 長上影 (遇壓)"
            elif close > open_p and body > (high_p - low_p) * 0.7:
                k_pattern = "📈 實體紅K"
            
            hist['MA5'], hist['MA20'], hist['MA60'] = hist['Close'].rolling(5).mean(), hist['Close'].rolling(20).mean(), hist['Close'].rolling(60).mean()
            vol_today, vol_ma5 = float(hist['Volume'].iloc[-1]), hist['Volume'].rolling(5).mean().iloc[-1]
            bb_width = (4 * hist['Close'].rolling(20).std()) / hist['MA20']
            
            rsv = (hist['Close'] - hist['Low'].rolling(9).min()) / (hist['High'].rolling(9).max() - hist['Low'].rolling(9).min()) * 100
            k_s = rsv.ewm(com=2).mean()
            dif = hist['Close'].ewm(span=12).mean() - hist['Close'].ewm(span=26).mean()
            osc = dif - dif.ewm(span=9).mean()
            
            obv = (np.sign(hist['Close'].diff()) * hist['Volume']).fillna(0).cumsum()
            obv_up = obv.iloc[-1] > obv.rolling(10).mean().iloc[-1]
            obv_high = obv.iloc[-1] >= obv.rolling(20).max().iloc[-1] * 0.95
            res_20 = hist['High'].rolling(20).max().shift(1).iloc[-1]
            
            try:
                hist_poc = hist.tail(20).copy()
                bins = np.linspace(hist_poc['Low'].min(), hist_poc['High'].max(), 40)
                hist_poc['Price_Bin'] = pd.cut((hist_poc['High']+hist_poc['Low']+hist_poc['Close'])/3, bins=bins, include_lowest=True)
                poc_price = hist_poc.groupby('Price_Bin')['Volume'].sum().idxmax().mid
            except: poc_price = close

            action = "🟡 盤整觀望"
            if close < hist['MA20'].iloc[-1]: 
                action = "🛑 破線防守"
            elif (k_s.iloc[-1] > k_s.iloc[-2] or osc.iloc[-1] > osc.iloc[-2]) and obv_up and obv_high and (close > res_20 or (res_20-close)/close > 0.05) and close > hist['MA60'].iloc[-1]:
                action = "🚀 波段起漲"
            elif close > hist['MA20'].iloc[-1] and close > hist['MA60'].iloc[-1]: 
                action = "🟢 多頭排列"

            is_dark_horse = "🐎 爆發準備" if (close > hist['MA20'].iloc[-1] and bb_width.iloc[-1] < 0.15 and obv_up) else "-"

            display_name = f"{name} ({symbol})"
            data_list.append({
                "代號": symbol, "所屬題材": SYMBOL_TO_THEME.get(full_symbol, "📌 自選股"),
                "指標股": display_name, "漲跌幅(%)": round(change_pct, 2), "現價": round(close, 2), 
                "K線型態": k_pattern, "POC鐵板價": round(poc_price, 2), 
                "波段策略": action, "黑馬潛力": is_dark_horse,
                "籌碼動能": "🔥 爆量" if vol_today > vol_ma5 * 1.5 else "-"
            })
            price_history_dict[display_name] = hist.tail(90)
        except: pass
    return pd.DataFrame(data_list), price_history_dict

def plot_advanced_k_volume(hist_df, name):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.15, 0.15, 0.2])
    trade_dates = hist_df.index.strftime('%y/%m/%d')
    
    fig.add_trace(go.Candlestick(x=trade_dates, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'], close=hist_df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=trade_dates, y=hist_df['MA5'], name='5MA', line=dict(color='#FFA500', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=trade_dates, y=hist_df['MA20'], name='20MA', line=dict(color='#1E90FF', width=1.8)), row=1, col=1)
    
    colors = ['#ff4b4b' if r['Close'] >= r['Open'] else '#00cc96' for i, r in hist_df.iterrows()]
    fig.add_trace(go.Bar(x=trade_dates, y=hist_df['Volume'], name='成交量', marker_color=colors), row=2, col=1)
    
    exp1 = hist_df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = hist_df['Close'].ewm(span=26, adjust=False).mean()
    dif = exp1 - exp2
    macd = dif.ewm(span=9, adjust=False).mean()
    osc = dif - macd
    osc_colors = ['#ff4b4b' if val >= 0 else '#00cc96' for val in osc]
    fig.add_trace(go.Bar(x=trade_dates, y=osc, name='MACD柱', marker_color=osc_colors), row=3, col=1)
    fig.add_trace(go.Scatter(x=trade_dates, y=dif, name='DIF', line=dict(color='#1E90FF', width=1.2)), row=3, col=1)
    
    obv = (np.sign(hist_df['Close'].diff()) * hist_df['Volume']).fillna(0).cumsum()
    obv_ma10 = obv.rolling(10).mean()
    fig.add_trace(go.Scatter(x=trade_dates, y=obv, name='OBV主力線', line=dict(color='#9932CC', width=2.2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=trade_dates, y=obv_ma10, name='OBV均線', line=dict(color='#ccc', width=1, dash='dot')), row=4, col=1)

    fig.update_layout(height=700, xaxis_rangeslider_visible=False, showlegend=False, margin=dict(t=30, b=10, r=10, l=10))
    fig.update_xaxes(type='category', nticks=15)
    return fig

def color_strategy(val):
    if any(x in str(val) for x in ["🚀", "🟢", "🐎", "📌", "📈"]): return 'color: #ff4b4b; font-weight: bold;'
    if any(x in str(val) for x in ["🛑", "⚠️"]): return 'color: #00cc96; font-weight: bold;'
    return ''

# ================= 4. UI 版面配置 =================
st.title("概覽")

with st.spinner("🚀 系統載入與核心運算中 (安全連線模式啟動，約需 10-15 秒請稍候)..."):
    flat_stock_dict = {sym: name for theme_dict in STOCK_DB.values() for sym, name in theme_dict.items()}
    df_all, hist_all = get_stock_data_v95(flat_stock_dict)

# --- 區塊 1：AI 市場摘要 ---
summary_text, tags = get_market_summary_and_tags()
st.markdown(f"""
<div class="summary-card">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; margin-right: 10px;">🤖 AI 市場摘要</span>
        <span style="color: #718096; font-size: 12px;">盤後整理</span>
    </div>
    <h4 style="margin-top: 0; color: #1a202c; font-size: 16px; line-height: 1.5;">{summary_text}</h4>
    <div style="margin-top: 15px;">{''.join([f'<span class="tag-pill">#{t}</span>' for t in tags])}</div>
</div>
""", unsafe_allow_html=True)

# --- 區塊 2：大盤動態區 ---
st.markdown("##### 大盤動態")
idx_data = get_indices()
cols_idx = st.columns(len(idx_data))
for i, (n, d) in enumerate(idx_data.items()):
    color = "#ff4b4b" if d['漲跌幅'] >= 0 else "#00cc96"
    arrow = "▲" if d['漲跌幅'] >= 0 else "▼"
    cols_idx[i].markdown(f"""
    <div class="metric-card">
        <div style="color: #718096; font-size: 14px;">{n}</div>
        <div style="font-size: 24px; font-weight: bold; color: #1a202c; margin: 5px 0;">{d['現價']:,}</div>
        <div style="color: {color}; font-size: 14px; font-weight: bold;">{arrow} {abs(d['漲跌幅'])}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 區塊 3：核心工具區 ---
tab_group, tab_trend, tab_darkhorse, tab_chart = st.tabs(["🔥 族群熱力圖", "🚀 波段起漲股", "🐎 潛在黑馬股", "🔍 線型 X光機"])

with tab_group:
    if not df_all.empty:
        st.write("各族群平均漲跌幅 (觀察資金流向)")
        group_df = df_all.groupby('所屬題材')['漲跌幅(%)'].mean().reset_index().sort_values("漲跌幅(%)", ascending=False)
        st.dataframe(group_df, width="stretch", hide_index=True)

with tab_trend:
    if not df_all.empty:
        st.write("技術面呈多頭排列，且籌碼與動能指標轉強之標的。")
        df_trend = df_all[df_all['波段策略'].str.contains("🚀|🟢")]
        st.dataframe(df_trend[['所屬題材', '指標股', '漲跌幅(%)', '現價', 'K線型態', 'POC鐵板價', '波段策略', '籌碼動能']].style.map(color_strategy, subset=['波段策略', 'K線型態']), width="stretch", hide_index=True)

with tab_darkhorse:
    if not df_all.empty:
        st.write("布林通道極度壓縮，且 OBV 主力籌碼暗中吃貨之打底標的。")
        df_darkhorse = df_all[df_all['黑馬潛力'].str.contains("🐎")]
        st.dataframe(df_darkhorse[['所屬題材', '指標股', '漲跌幅(%)', '現價', 'K線型態', 'POC鐵板價', '黑馬潛力', '籌碼動能']].style.map(color_strategy, subset=['黑馬潛力', 'K線型態']), width="stretch", hide_index=True)

with tab_chart:
    st.write("輸入代號，調閱完整技術指標與量能 (含 K線、成交量、MACD、OBV)")
    search_sym = st.text_input("🎯 輸入全台任意代號 (如: 2330)", "")
    if search_sym:
        with st.spinner("分析中..."):
            s_hist, s_name = fetch_single_stock(search_sym)
            if s_hist is not None: 
                st.plotly_chart(plot_advanced_k_volume(s_hist, s_name), width="stretch")
            else: 
                st.error("找不到該代號，請確認輸入是否正確。")
