import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Configuração e Refresh
st.set_page_config(page_title="VVG Terminal Pro", layout="wide")
st_autorefresh(interval=15000, key="vvg_v4_organized")

# Estilo Visual Terminal
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMarkdown, p, h3, h2, h1 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    .stTable { background-color: #050505; color: #ffffff; border: 1px solid #333; }
    thead th { color: #FFFF00 !important; }
    hr { border: 0.5px solid #333; }
    </style>
    """, unsafe_allow_html=True)

def buscar_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=2d"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['close'] = df['close'].ffill()
        return df, r['meta']['regularMarketPrice']
    except: return None, 0

def calcular_sinais(df):
    if df is None or len(df) < 50: return {}
    c = df['close']
    s = {}
    s['EMA 9'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=9).iloc[-1] else "🔴 VENDA"
    s['EMA 21'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=21).iloc[-1] else "🔴 VENDA"
    rsi = ta.rsi(c, length=14).iloc[-1]
    s['RSI (14)'] = "🟢 COMPRA" if rsi < 40 else ("🔴 VENDA" if rsi > 60 else "⚪ NEUTRO")
    macd = ta.macd(c)
    s['MACD'] = "🟢 COMPRA" if macd.iloc[-1, 0] > macd.iloc[-1, 2] else "🔴 VENDA"
    bb = ta.bbands(c, length=20)
    if bb is not None:
        if c.iloc[-1] < bb.iloc[-1, 0]: s['Bollinger'] = "🟢 COMPRA"
        elif c.iloc[-1] > bb.iloc[-1, 2]: s['Bollinger'] = "🔴 VENDA"
        else: s['Bollinger'] = "⚪ NEUTRO"
    return s

def painel_medias(df):
    if df is None or len(df) < 55: return []
    c = df['close']
    periodos = [5, 10, 20, 50]
    lista_ma = []
    for p in periodos:
        ma = ta.sma(c, length=p).iloc[-1]
        sinal = "🟢 COMPRA" if c.iloc[-1] > ma else "🔴 VENDA"
        lista_ma.append([f"MA {p}", sinal])
    return lista_ma

# --- Interface Principal ---
df1, preco = buscar_dados("1m")
df5, _ = buscar_dados("5m")

st.write(f"### 🖥️ TERMINAL VVG | EUR/USD: {preco:.5f}")
st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

if df1 is not None:
    # --- BLOCO 1: INDICADORES TÉCNICOS ---
    st.markdown("### 📊 INDICADORES TÉCNICOS")
    ind1, ind5 = calcular_sinais(df1), calcular_sinais(df5)
    tabela_ind = [[k, ind1[k], ind5.get(k, "⚪ ---")] for k in ind1.keys()]
    st.table(pd.DataFrame(tabela_ind, columns=["INDICADOR", "M1", "M5"]))
    
    # Força dos Indicadores (Logo abaixo da tabela)
    c_ind = sum(1 for v in ind1.values() if "COMPRA" in v)
    f_ind = (c_ind / len(ind1)) * 100
    st.write(f"⚡ **FORÇA DOS INDICADORES:** {f_ind:.0f}% COMPRA")
    st.progress(f_ind/100)
    
    st.markdown("---")

    # --- BLOCO 2: MÉDIAS MÓVEIS ---
    st.markdown("### 📈 MÉDIAS MÓVEIS")
    ma1 = painel_medias(df1)
    ma5 = painel_medias(df5)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("⏱️ **M1**")
        st.table(pd.DataFrame(ma1, columns=["PERÍODO", "SINAL"]))
    with col2:
        st.write("⏱️ **M5**")
        st.table(pd.DataFrame(ma5, columns=["PERÍODO", "SINAL"]))
    
    # Força das Médias (Logo abaixo das tabelas)
    c_ma = sum(1 for m in ma1 if "COMPRA" in m[1])
    f_ma = (c_ma / len(ma1)) * 100
    st.write(f"⚡ **FORÇA DAS MÉDIAS:** {f_ma:.0f}% COMPRA")
    st.progress(f_ma/100)

    st.markdown("---")

    # --- BLOCO 3: VEREDITO FINAL ---
    forca_total = (f_ind + f_ma) / 2
    if forca_total > 70:
        st.success(f"🚀 **COMPRA FORTE ({forca_total:.0f}%)**")
    elif forca_total < 30:
        st.error(f"📉 **VENDA FORTE ({forca_total:.0f}%)**")
    else:
        st.warning(f"⚖️ **NEUTRO / AGUARDAR ({forca_total:.0f}%)**")
        
