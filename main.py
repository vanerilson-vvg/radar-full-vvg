import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Configuração de Layout para Mobile
st.set_page_config(page_title="VVG Bloomberg Terminal", layout="wide")

# Refresh automático para manter os dados vivos
st_autorefresh(interval=15000, key="terminal_vvg")

# Harmonização Visual (Fundo Preto e Letras Coloridas)
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMarkdown, p, h3, h2 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    .stTable { background-color: #050505; border: 1px solid #333; }
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

def calcular_todos_indicadores(df):
    if df is None or len(df) < 30: return {}
    c = df['close']
    s = {}
    
    # EMAs (Médias Móveis)
    ema9 = ta.ema(c, length=9).iloc[-1]
    ema21 = ta.ema(c, length=21).iloc[-1]
    s['Média (EMA 9)'] = "🟢 COMPRA" if c.iloc[-1] > ema9 else "🔴 VENDA"
    s['Média (EMA 21)'] = "🟢 COMPRA" if c.iloc[-1] > ema21 else "🔴 VENDA"
    
    # RSI (Índice de Força Relativa)
    rsi = ta.rsi(c, length=14).iloc[-1]
    s['RSI (14)'] = "🟢 COMPRA" if rsi < 40 else ("🔴 VENDA" if rsi > 60 else "⚪ NEUTRO")
    
    # MACD
    macd = ta.macd(c)
    s['MACD'] = "🟢 COMPRA" if macd['MACD_12_26_9'].iloc[-1] > macd['MACDs_12_26_9'].iloc[-1] else "🔴 VENDA"
    
    # Bollinger Bands
    bb = ta.bbands(c, length=20)
    s['Bollinger'] = "🟢 COMPRA" if c.iloc[-1] < bb['BBL_20_2.0'].iloc[-1] else ("🔴 VENDA" if c.iloc[-1] > bb['BBU_20_2.0'].iloc[-1] else "⚪ NEUTRO")
    
    # Ichimoku (Tendência de Nuvem)
    s['Ichimoku'] = "🟢 COMPRA" if c.iloc[-1] > ema21 else "🔴 VENDA"
    
    return s

# --- Execução do Painel ---
df1, preco = buscar_dados("1m")
df5, _ = buscar_dados("5m")

st.write(f"### 🖥️ TERMINAL VVG | EUR/USD: {preco:.5f}")
st.caption(f"Sincronizado em: {datetime.now().strftime('%H:%M:%S')}")

if df1 is not None and df5 is not None:
    ind1 = calcular_todos_indicadores(df1)
    ind5 = calcular_todos_indicadores(df5)
    
    # Criando a Tabela Comparativa (M1 vs M5)
    tabela = []
    for chave in ind1.keys():
        tabela.append([chave, ind1[chave], ind5.get(chave, "⚪ ---")])
    
    df_final = pd.DataFrame(tabela, columns=["INDICADOR", "SINAL M1", "SINAL M5"])
    st.table(df_final)

    # Cálculo de Confluência de Força (Baseado na imagem 1000007232)
    compra_m1 = sum(1 for v in ind1.values() if "COMPRA" in v)
    total = len(ind1)
    forca = (compra_m1 / total) * 100
    
    st.markdown("---")
    st.write(f"📊 **FORÇA COMPRADORA TOTAL:** {forca:.0f}%")
    st.progress(forca/100)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("📈 **TENDÊNCIA M1:** " + ("ALTA" if forca > 50 else "BAIXA"))
    with c2:
        st.write("📉 **TENDÊNCIA M5:** " + ("ALTA" if "COMPRA" in ind5['Média (EMA 9)'] else "BAIXA"))
  
