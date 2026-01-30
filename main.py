import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Configuração e Refresh
st.set_page_config(page_title="VVG Terminal Ultra", layout="wide")
st_autorefresh(interval=15000, key="vvg_final_ma")

# Estilo Visual Bloomberg
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMarkdown, p, h3, h2 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    .stTable { background-color: #050505; color: #ffffff; border: 1px solid #333; }
    thead th { color: #FFFF00 !important; }
    </style>
    """, unsafe_allow_html=True)

def buscar_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=5d"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['close'] = df['close'].ffill()
        return df, r['meta']['regularMarketPrice']
    except: return None, 0

def calcular_sinais(df):
    if df is None or len(df) < 100: return {}
    c = df['close']
    s = {}
    
    # Indicadores Principais
    s['Média (EMA 9)'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=9).iloc[-1] else "🔴 VENDA"
    s['Média (EMA 21)'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=21).iloc[-1] else "🔴 VENDA"
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
    if df is None or len(df) < 100: return []
    c = df['close']
    periodos = [1, 5, 10, 20, 50, 100]
    lista_ma = []
    for p in periodos:
        ma = ta.sma(c, length=p).iloc[-1]
        sinal = "🟢 CPR" if c.iloc[-1] > ma else "🔴 VND"
        lista_ma.append([f"MA {p}M", sinal])
    return lista_ma

# --- Execução ---
df1, preco = buscar_dados("1m")
df5, _ = buscar_dados("5m")

st.write(f"### 🖥️ TERMINAL VVG | EUR/USD: {preco:.5f}")
st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

if df1 is not None and df5 is not None:
    # 1. Tabela de Indicadores
    ind1, ind5 = calcular_sinais(df1), calcular_sinais(df5)
    tabela = [[k, ind1[k], ind5.get(k, "⚪ ---")] for k in ind1.keys()]
    st.table(pd.DataFrame(tabela, columns=["INDICADOR", "SINAL M1", "SINAL M5"]))
    
    # 2. SEÇÃO DE MÉDIAS MÓVEIS (NOVIDADE)
    st.markdown("### 📈 MÉDIAS MÓVEIS DETALHADAS")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("⏱️ **TEMPO 1 MINUTO**")
        ma1 = painel_medias(df1)
        st.table(pd.DataFrame(ma1, columns=["PERÍODO", "SINAL"]))
        
    with col2:
        st.write("⏱️ **TEMPO 5 MINUTOS**")
        ma5 = painel_medias(df5)
        st.table(pd.DataFrame(ma5, columns=["PERÍODO", "SINAL"]))

    # 3. Barras de Força
    qtd_compra = sum(1 for v in ind1.values() if "COMPRA" in v)
    forca_c = (qtd_compra / len(ind1)) * 100
    forca_v = 100 - forca_c
    
    st.markdown("---")
    st.write(f"🟢 **FORÇA COMPRADORA:** {forca_c:.0f}%")
    st.progress(forca_c/100)
    st.write(f"🔴 **FORÇA VENDEDORA:** {forca_v:.0f}%")
    st.progress(forca_v/100)
    
