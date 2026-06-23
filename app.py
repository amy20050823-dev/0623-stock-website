import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import time

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

# 💡 V97 核心進化：自動從後台讀取密鑰，完全隱藏真實 Key
try:
    fugle_key = st.secrets["general"]["fugle_key"]
except (KeyError, FileNotFoundError):
    st.error("⚠️ 系統偵測到未設定 API Key！請至 Streamlit 後台的 Settings -> Secrets 進行設定。")
    st.stop()

if 'custom_themes' not in st.session_state:
    st.session_state['custom_themes'] = {}

# ================= 2. 核心資料庫 =================
BASE_STOCK_DB = {
    "AI伺服器": {"2330": "台積電", "2317": "鴻海", "2382": "廣達", "3231": "緯創", "2376": "技嘉", "6669": "緯穎", "3706": "神達", "2356": "英業達"},
    "散熱與水冷": {"3017": "奇鋐", "3324": "雙鴻", "2421": "建準", "8996": "高力", "3483": "力致", "3653": "健策"},
    "電源與BBU": {"2308": "台達電", "2301": "光寶科", "6409": "旭隼", "6121": "新普", "6781": "AES-KY", "3211": "順達"},
    "CoWoS封裝": {"3131": "弘塑", "6187": "萬潤", "5443": "均豪", "6640": "均華", "3583": "辛耘", "6515": "穎崴"},
    "矽光子CPO": {"4979": "華星光", "3450": "聯鈞", "3081": "聯亞", "3363": "上詮", "6442": "光聖", "3163": "波若威"},
    "特化與光阻": {"4770": "上品", "1773": "勝一", "4755": "三福化", "1727": "中華化", "4763": "材料-KY"},
    "面板級封測": {"3711": "日月光投控", "2449": "京元電子", "6257": "矽格", "3481": "群創", "8064": "東捷"},
    "廠務與無塵室": {"2404": "漢唐", "3402": "漢科", "6139": "亞翔", "5536": "聖暉*"},
    "IP矽智財": {"3443": "智原", "3661": "世芯-KY", "6643": "M31", "6533": "晶心科", "3529": "力旺"},
    "ABF載板": {"3037": "欣興", "8046": "南電", "3189": "景碩"},
    "網通與光通訊": {"3596": "智易", "5388": "中磊", "3380": "明泰", "6285": "啟碁"},
    "低軌衛星": {"2313": "華通", "3491": "昇達科", "6271": "同欣電", "2485": "兆赫"},
    "機器人與自動化": {"2359": "所羅門", "2365": "昆盈", "6414": "樺漢", "8374": "羅昇", "2049": "上銀"},
    "AI PC": {"2357": "華碩", "2353": "宏碁", "2395": "研華", "8114": "振樺電"},
    "功率元件": {"8255": "朋程", "3645": "達邁", "5425": "台半", "8261": "富鼎", "3317": "尼克森"} 
}
STOCK_DB = {**BASE_STOCK_DB, **st.session_state['custom_themes']}
SYMBOL_TO_THEME = {sym: theme for theme, stocks in STOCK_DB.items() for sym in stocks}
LEADERS = ["2330", "2317", "3450", "4979", "3037", "2383", "3017", "2308", "2327", "2454", "3661"]

# ================= 3. 富果 API 核心數據引擎 =================
def fetch_fugle_kline(symbol, api_key):
    try:
        headers = {"X-API-KEY": api_key}
        url = f"https://api.fugle.tw/marketdata/v1.0/stock/historical/candles/{symbol}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if 'candles' in data and data['candles']:
                df = pd.DataFrame(data['candles'])
                df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume', 'date': 'Date'})
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date').reset_index(drop=True)
                df.set_index('Date', inplace=True)
                return df
    except: pass
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_market_summary_and_tags():
    try:
        url_tw = "https://tw.news.yahoo.com/rss/stock"
        res = requests.get(url_tw, headers={'User-Agent':'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'xml')
        titles = [item.title.text for item in soup.find_all('item')[:8]]
        if titles:
            summary_text = "今日盤面焦點： " + "；".join(titles[:3]) + "。資金輪動快速，建議留意籌碼與月線防守。"
            all_text = "".join(titles)
            keywords = ["台積電", "AI", "外資", "散熱", "鴻海", "聯發科", "降息", "營收", "半導體", "漲停"]
            found_tags = [kw for kw in keywords if kw in all_text]
            tags = found_tags[:4] if found_tags else ["盤整", "觀望"]
        else:
            summary_text = "目前市場無重大突發消息，呈現量縮整理格局。"
            tags = ["平穩", "量縮"]
        return summary_text, tags
    except:
        return "資金流向觀測中，建議留意權值股動態與均線支撐。", ["台股", "半導體"]

@st.cache_data(ttl=600)
def get_all_stock_data(stock_dict, api_key):
    data_list, price_history_dict = [], {}
    
    for symbol, name in stock_dict.items():
        hist = fetch_fugle_kline(symbol, api_key)
        if hist.empty or len(hist) < 15: continue
        
        try:
            close_p = float(hist['Close'].iloc[-1])
            prev_close = float(hist['Close'].iloc[-2])
            open_p = float(hist['Open'].iloc[-1])
            high_p = float(hist['High'].iloc[-1])
            low_p = float(hist['Low'].iloc[-1])
            change_pct = ((close_p - prev_close) / prev_close) * 100
            
            upper_shadow = high_p - max(open_p, close_p)
            lower_shadow = min(open_p, close_p) - low_p
            body = abs(open_p - close_p)
            
            k_pattern = "-"
            if lower_shadow > body * 1.5 and lower_shadow > upper_shadow: k_pattern = "📌 長下影 (探底)"
            elif upper_shadow > body * 1.5 and upper_shadow > lower_shadow: k_pattern = "⚠️ 長上影 (遇壓)"
            elif close_p > open_p and body > (high_p - low_p) * 0.7: k_pattern = "📈 實體紅K"
            
            hist['MA5'] = hist['Close'].rolling(5).mean()
            hist['MA20'] = hist['Close'].rolling(20).mean()
            vol_today = float(hist['Volume'].iloc[-1])
            vol_ma5 = hist['Volume'].rolling(5).mean().iloc[-1]
            
            bb_std = hist['Close'].rolling(20).std().iloc[-1]
            bb_ma20 = hist['MA20'].iloc[-1]
            bb_width = (4 * bb_std) / bb_ma20 if bb_ma20 > 0 else 1.0
            
            obv = (np.sign(hist['Close'].diff()) * hist['Volume']).fillna(0).cumsum()
            obv_up = obv.iloc[-1] > obv.rolling(10).mean().iloc[-1]
            
            try:
                hist_poc = hist.tail(15).copy()
                poc_price = (hist_poc['High'].max() + hist_poc['Low'].min()) / 2
            except: poc_price = close_p
            
            action = "🟡 盤整觀望"
            if close_p < bb_ma20: action = "🛑 破線防守"
            elif close_p > bb_ma20 and obv_up: action = "🚀 波段起漲"
            
            is_dark_horse = "🐎 爆發準備" if (close_p > bb_ma20 and bb_width < 0.18 and obv_up) else "-"
            
            display_name = f"{name} ({symbol})"
            if symbol in LEADERS: display_name = f"👑 {display_name}"
            
            data_list.append({
                "代號": symbol, "所屬題材": SYMBOL_TO_THEME.get(symbol, "📌 自選"),
                "指標股": display_name, "漲跌幅(%)": round(change_pct, 2), "現價": round(close_p, 2),
                "K線型態": k_pattern, "POC鐵板價": round(poc_price, 2),
                "波段策略": action, "黑馬潛力": is_dark_horse, "籌碼動能": "🔥 爆量" if vol_today > vol_ma5 * 1.5 else "-"
            })
            price_history_dict[display_name] = hist.tail(40)
        except: pass
        
    return pd.DataFrame(data_list), price_history_dict

# ================= 4. UI 介面佈局 =================
st.title("概覽")

with st.spinner("🚀 正在經由 富果(Fugle) 安全隧道初始化全台股題材庫..."):
    flat_dict = {sym: name for t in STOCK_DB.values() for sym, name in t.items()}
    df_all, hist_all = get_all_stock_data(flat_dict, fugle_key)

# --- 區塊 1：AI 市場摘要 ---
summary_text, tags = get_market_summary_and_tags()
st.markdown(f"""
<div class="summary-card">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 12px; margin-right: 10px;">🤖 AI 市場摘要</span>
        <span style="color: #718096; font-size: 12px;">智慧防護版</span>
    </div>
    <h4 style="margin-top: 0; color: #1a202c; font-size: 16px; line-height: 1.5;">{summary_text}</h4>
    <div style="margin-top: 15px;">{''.join([f'<span class="tag-pill">#{t}</span>' for t in tags])}</div>
</div>
""", unsafe_allow_html=True)

# --- 區塊 2：大盤動態區 (靜態安全鎖) ---
st.markdown("##### 大盤動態")
col_i1, col_i2, col_i3, col_i4 = st.columns(4)
col_i1.markdown('<div class="metric-card"><div style="color:#718096;font-size:14px;">加權指數</div><div style="font-size:24px;font-weight:bold;color:#1a202c;margin:5px 0;">22,430.15</div><div style="color:#ff4b4b;font-size:14px;font-weight:bold;">▲ 0.85%</div></div>', unsafe_allow_html=True)
col_i2.markdown('<div class="metric-card"><div style="color:#718096;font-size:14px;">台指期近月</div><div style="font-size:24px;font-weight:bold;color:#1a202c;margin:5px 0;">22,455.00</div><div style="color:#ff4b4b;font-size:14px;font-weight:bold;">▲ 0.92%</div></div>', unsafe_allow_html=True)
col_i3.markdown('<div class="metric-card"><div style="color:#718096;font-size:14px;">台積電 ADR</div><div style="font-size:24px;font-weight:bold;color:#1a202c;margin:5px 0;">172.50</div><div style="color:#ff4b4b;font-size:14px;font-weight:bold;">▲ 1.45%</div></div>', unsafe_allow_html=True)
col_i4.markdown('<div class="metric-card"><div style="color:#718096;font-size:14px;">費城半導體</div><div style="font-size:24px;font-weight:bold;color:#1a202c;margin:5px 0;">5,130.40</div><div style="color:#00cc96;font-size:14px;font-weight:bold;">▼ -0.32%</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- 區塊 3：分頁掃描區 ---
tab_group, tab_trend, tab_darkhorse, tab_chart = st.tabs(["🔥 族群熱力圖", "🚀 波段起漲股", "🐎 潛在黑馬股", "🔍 線型 X光機"])

def color_strategy(val):
    if any(x in str(val) for x in ["🚀", "🟢", "🐎", "📌", "📈"]): return 'color: #ff4b4b; font-weight: bold;'
    if "🛑" in str(val): return 'color: #00cc96; font-weight: bold;'
    return ''

with tab_group:
    if not df_all.empty:
        group_df = df_all.groupby('所屬題材')['漲跌幅(%)'].mean().reset_index().sort_values("漲跌幅(%)", ascending=False)
        st.dataframe(group_df, width="stretch", hide_index=True)

with tab_trend:
    if not df_all.empty:
        df_trend = df_all[df_all['波段策略'].str.contains("🚀|🟢")]
        st.dataframe(df_trend[['所屬題材', '指標股', '漲跌幅(%)', '現價', 'K線型態', 'POC鐵板價', '波段策略', '籌碼動能']].style.map(color_strategy, subset=['波段策略', 'K線型態']), width="stretch", hide_index=True)

with tab_darkhorse:
    if not df_all.empty:
        df_dark = df_all[df_all['黑馬潛力'].str.contains("🐎")]
        st.dataframe(df_dark[['所屬題材', '指標股', '漲跌幅(%)', '現價', 'K線型態', 'POC鐵板價', '黑馬潛力', '籌碼動能']].style.map(color_strategy, subset=['黑馬潛力', 'K線型態']), width="stretch", hide_index=True)

with tab_chart:
    st.write("請從下方清單選擇個股調閱富果 K 線圖：")
    if not df_all.empty:
        sel_stock = st.selectbox("選擇股票", df_all['指標股'].tolist())
        if sel_stock in hist_all:
            h = hist_all[sel_stock]
            t_dates = h.index.strftime('%m/%d')
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=t_dates, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name='K線'), row=1, col=1)
            fig.add_trace(go.Scatter(x=t_dates, y=h['MA20'], name='20MA(月線)', line=dict(color='#1E90FF')), row=1, col=1)
            colors = ['#ff4b4b' if r['Close'] >= r['Open'] else '#00cc96' for i, r in h.iterrows()]
            fig.add_trace(go.Bar(x=t_dates, y=h['Volume'], name='成交量', marker_color=colors), row=2, col=1)
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
