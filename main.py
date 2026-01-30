import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Configuração de Layout e Refresh Automático (15 segundos)
st.set_page_config(page_title="VVG Terminal Pro", layout="wide")
st_autorefresh(interval=15000, key="vvg_final")

# Estilo Visual Bloomberg/Neon
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMarkdown, p, h3, h2 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    .stTable { background-color: #050505; color: #ffffff; border: 1px solid #333; }
    thead th { color: #FFFF00 !important; }
    </style>
    """, unsafe_allow_html=True)

def buscar_dados(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=1d"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        r = res.json()['chart']['result'][0]
        df = pd.DataFrame(r['indicators']['quote'][0])
        df['close'] = df['close'].ffill()
        return df, r['meta']['regularMarketPrice']
    except: return None, 0

def calcular_sinais(df):
    if df is None or len(df) < 30: return {}
    c = df['close']
    s = {}
    
    # Médias Móveis (EMA)
    ema9 = ta.ema(c, length=9).iloc[-1]
    ema21 = ta.ema(c, length=21).iloc[-1]
    s['Média (EMA 9)'] = "🟢 COMPRA" if c.iloc[-1] > ema9 else "🔴 VENDA"
    s['Média (EMA 21)'] = "🟢 COMPRA" if c.iloc[-1] > ema21 else "🔴 VENDA"
    
    # RSI (Índice de Força Relativa)
    rsi = ta.rsi(c, length=14).iloc[-1]
    s['RSI (14)'] = "🟢 COMPRA" if rsi < 40 else ("🔴 VENDA" if rsi > 60 else "⚪ NEUTRO")
    
    # MACD
    macd = ta.macd(c)
    s['MACD'] = "🟢 COMPRA" if macd.iloc[-1, 0] > macd.iloc[-1, 2] else "🔴 VENDA"
    
    # Bandas de Bollinger
    bb = ta.bbands(c, length=20)
    if bb is not None:
        if c.iloc[-1] < bb.iloc[-1, 0]: s['Bollinger'] = "🟢 COMPRA"
        elif c.iloc[-1] > bb.iloc[-1, 2]: s['Bollinger'] = "🔴 VENDA"
        else: s['Bollinger'] = "⚪ NEUTRO"
    else: s['Bollinger'] = "⚪ ---"
    
    return s

# --- Lógica de Exibição ---
df1, preco = buscar_dados("1m")
df5, _ = buscar_dados("5m")

st.write(f"### 🖥️ TERMINAL VVG | EUR/USD: {preco:.5f}")
st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

if df1 is not None and df5 is not None:
    ind1, ind5 = calcular_sinais(df1), calcular_sinais(df5)
    tabela = [[k, ind1[k], ind5.get(k, "⚪ ---")] for k in ind1.keys()]
    st.table(pd.DataFrame(tabela, columns=["INDICADOR", "SINAL M1", "SINAL M5"]))
    
    # --- CÁLCULO DE FORÇA (COMPRA VS VENDA) ---
    total = len(ind1)
    qtd_compra = sum(1 for v in ind1.values() if "COMPRA" in v)
    qtd_venda = sum(1 for v in ind1.values() if "VENDA" in v)
    
    forca_compra = (qtd_compra / total) * 100
    forca_venda = (qtd_venda / total) * 100
    
    st.markdown("---")
    
    # Exibição da Força Compradora (Verde)
    st.write(f"🟢 **FORÇA COMPRADORA (M1):** {forca_compra:.0f}%")
    st.progress(forca_compra/100)
    
    # Exibição da Força Vendedora (Vermelha)
    st.write(f"🔴 **FORÇA VENDEDORA (M1):** {forca_venda:.0f}%")
    st.progress(forca_venda/100)

    # Resumo de Tendência Final
    if forca_compra > 60:
        st.success("🔥 TENDÊNCIA DE ALTA FORTE")
    elif forca_venda > 60:
        st.error("📉 TENDÊNCIA DE BAIXA FORTE")
    else:
        st.warning("⚖️ MERCADO EM LATERALIZAÇÃO (NEUTRO)")
    
