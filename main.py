import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ATUALIZAÇÃO ULTRA RÁPIDA (2 SEGUNDOS)
st.set_page_config(page_title="VVG Terminal Pro", layout="wide")
st_autorefresh(interval=2000, key="vvg_v9_top_force")

# Estilo Visual Terminal
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMarkdown, p, h3, h2, h1 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    .stTable { background-color: #050505; color: #ffffff; border: 1px solid #333; }
    thead th { color: #FFFF00 !important; }
    hr { border: 0.5px solid #333; }
    .price-main { color: #00FF00; font-size: 26px; font-weight: bold; margin-bottom: 0px; }
    .price-mt5 { color: #FFFF00; font-size: 20px; font-weight: bold; margin-top: -10px; }
    .price-down { color: #FF0000; font-size: 26px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def buscar_dados_completos(intervalo):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=2d"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
        data = res.json()['chart']['result'][0]
        df = pd.DataFrame(data['indicators']['quote'][0])
        df['close'] = df['close'].ffill()
        preco_atual = data['meta']['regularMarketPrice']
        preco_anterior = data['meta']['previousClose']
        return df, preco_atual, preco_anterior
    except: return None, 0, 0

def calcular_sinais(df):
    if df is None or len(df) < 50: return {}
    c = df['close']; s = {}
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
    c = df['close']; periodos = [5, 10, 20, 50]; lista_ma = []
    for p in periodos:
        ma = ta.sma(c, length=p).iloc[-1]
        sinal = "🟢 COMPRA" if c.iloc[-1] > ma else "🔴 VENDA"
        lista_ma.append([f"MA {p}", sinal])
    return lista_ma

# --- Execução e Cálculos ---
df1, preco, anterior = buscar_dados_completos("1m")
df5, _, _ = buscar_dados_completos("5m")

if df1 is not None:
    # Preparação dos dados para as forças
    ind1 = calcular_sinais(df1)
    ma1 = painel_medias(df1)
    
    # Reajuste de 4 pontos (0.00040)
    preco_reajustado = preco - 0.00040 
    variacao = preco - anterior
    pips = variacao * 10000
    cor_classe = "price-main" if variacao >= 0 else "price-down"

    # --- Interface Principal (CABECALHO) ---
    st.markdown(f"### 🖥️ TERMINAL VVG | EUR/USD")
    st.markdown(f'<p class="{cor_classe}">{preco:.5f} <span style="font-size:16px;">({pips:.1f} Pips)</span></p>', unsafe_allow_html=True)
    st.markdown(f'<p class="price-mt5">MT5: {preco_reajustado:.5f}</p>', unsafe_allow_html=True)
    
    st.markdown("---")

    # --- BLOCO DE FORÇAS (REPOSICIONADO PARA CIMA) ---
    st.markdown("### 📊 FORÇA DO MERCADO (M1)")
    
    # Força Indicadores
    f_ind = (sum(1 for v in ind1.values() if "COMPRA" in v) / len(ind1)) * 100
    status_ind = "🟢" if f_ind > 50 else "⚪" if f_ind == 50 else "🔴"
    st.write(f"{status_ind} **INDICADORES TÉCNICOS:** {f_ind:.0f}%")
    st.progress(f_ind/100)
    
    # Força Médias
    f_ma = (sum(1 for m in ma1 if "COMPRA" in m[1]) / len(ma1)) * 100
    status_ma = "🟢" if f_ma > 50 else "⚪" if f_ma == 50 else "🔴"
    st.write(f"{status_ma} **MÉDIAS MÓVEIS:** {f_ma:.0f}%")
    st.progress(f_ma/100)

    # Veredito Rápido
    forca_total = (f_ind + f_ma) / 2
    if forca_total > 70: st.success(f"🚀 **COMPRA FORTE ({forca_total:.0f}%)**")
    elif forca_total < 30: st.error(f"📉 **VENDA FORTE ({forca_total:.0f}%)**")
    
    st.markdown("---")

    # --- TABELAS DE DADOS (AGORA EMBAIXO DAS FORÇAS) ---
    st.markdown("### 📝 DETALHES DOS SINAIS")
    ind5 = calcular_sinais(df5)
    st.table(pd.DataFrame([[k, ind1[k], ind5.get(k, "⚪ ---")] for k in ind1.keys()], columns=["INDICADOR", "M1", "M5"]))
    
    col1, col2 = st.columns(2)
    ma5 = painel_medias(df5)
    with col1: st.write("⏱️ **MA - 1M**"); st.table(pd.DataFrame(ma1, columns=["PERÍODO", "SINAL"]))
    with col2: st.write("⏱️ **MA - 5M**"); st.table(pd.DataFrame(ma5, columns=["PERÍODO", "SINAL"]))

    st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")
    
