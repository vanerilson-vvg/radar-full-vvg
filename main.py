import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ATUALIZAÇÃO ULTRA RÁPIDA (2 SEGUNDOS)
st.set_page_config(page_title="VVG Terminal Pro", layout="wide")
st_autorefresh(interval=2000, key="vvg_v11_balanced")

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
    c = df['close']
    s = {}
    
    # 1. EMA 9 e 21 (Simetria Total)
    ema9 = ta.ema(c, length=9).iloc[-1]
    ema21 = ta.ema(c, length=21).iloc[-1]
    s['EMA 9'] = "🟢 COMPRA" if c.iloc[-1] > ema9 else "🔴 VENDA"
    s['EMA 21'] = "🟢 COMPRA" if c.iloc[-1] > ema21 else "🔴 VENDA"
    
    # 2. RSI (Ajustado para 50 como divisor de águas)
    rsi = ta.rsi(c, length=14).iloc[-1]
    if rsi > 55: s['RSI (14)'] = "🔴 VENDA"
    elif rsi < 45: s['RSI (14)'] = "🟢 COMPRA"
    else: s['RSI (14)'] = "⚪ NEUTRO"
    
    # 3. MACD (Cruzamento de linha zero e sinal)
    macd = ta.macd(c)
    # Linha MACD > Sinal = Compra | Linha MACD < Sinal = Venda
    s['MACD'] = "🟢 COMPRA" if macd.iloc[-1, 0] > macd.iloc[-1, 2] else "🔴 VENDA"
    
    # 4. Bandas de Bollinger (Reativo)
    bb = ta.bbands(c, length=20)
    if bb is not None:
        # Preço acima da média da banda = viés de venda (exaustão) ou vice-versa
        if c.iloc[-1] > bb.iloc[-1, 2]: s['Bollinger'] = "🔴 VENDA"
        elif c.iloc[-1] < bb.iloc[-1, 0]: s['Bollinger'] = "🟢 COMPRA"
        else: s['Bollinger'] = "⚪ NEUTRO"
    return s

def painel_medias(df):
    if df is None or len(df) < 55: return []
    c = df['close']
    periodos = [5, 10, 20, 50]
    lista_ma = []
    for p in periodos:
        ma = ta.sma(c, length=p).iloc[-1]
        # Se preço é menor ou IGUAL à média, já sinaliza venda para maior sensibilidade
        sinal = "🟢 COMPRA" if c.iloc[-1] > ma else "🔴 VENDA"
        lista_ma.append([f"MA {p}", sinal])
    return lista_ma

# --- Execução Principal ---
df1, preco, anterior = buscar_dados_completos("1m")
df5, _, _ = buscar_dados_completos("5m")

if df1 is not None:
    preco_reajustado = preco - 0.00040 
    variacao = preco - anterior
    pips = variacao * 10000
    cor_classe = "price-main" if variacao >= 0 else "price-down"

    # Cabeçalho
    st.markdown(f"### 🖥️ TERMINAL VVG | EUR/USD")
    st.markdown(f'<p class="{cor_classe}">{preco:.5f} <span style="font-size:16px;">({pips:.1f} Pips)</span></p>', unsafe_allow_html=True)
    st.markdown(f'<p class="price-mt5">MT5: {preco_reajustado:.5f}</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabelas
    st.markdown("### 📊 INDICADORES TÉCNICOS")
    ind1, ind5 = calcular_sinais(df1), calcular_sinais(df5)
    st.table(pd.DataFrame([[k, ind1[k], ind5.get(k, "⚪ ---")] for k in ind1.keys()], columns=["INDICADOR", "M1", "M5"]))
    
    # Força Indicadores
    c_ind = sum(1 for v in ind1.values() if "COMPRA" in v)
    f_ind = (c_ind / len(ind1)) * 100
    status_ind = "🟢" if f_ind > 50 else "⚪" if f_ind == 50 else "🔴"
    st.write(f"{status_ind} **FORÇA INDICADORES (M1):** {f_ind:.0f}%")
    st.progress(f_ind/100)
    
    st.markdown("---")

    st.markdown("### 📈 MÉDIAS MÓVEIS")
    ma1, ma5 = painel_medias(df1), painel_medias(df5)
    col1, col2 = st.columns(2)
    with col1: st.write("⏱️ **M1**"); st.table(pd.DataFrame(ma1, columns=["PERÍODO", "SINAL"]))
    with col2: st.write("⏱️ **M5**"); st.table(pd.DataFrame(ma5, columns=["PERÍODO", "SINAL"]))
    
    # Força Médias
    c_ma = sum(1 for m in ma1 if "COMPRA" in m[1])
    f_ma = (c_ma / len(ma1)) * 100
    status_ma = "🟢" if f_ma > 50 else "⚪" if f_ma == 50 else "🔴"
    st.write(f"{status_ma} **FORÇA MÉDIAS (M1):** {f_ma:.0f}%")
    st.progress(f_ma/100)

    st.markdown("---")

    # Veredito Final (Lógica de Venda espelhada na de Compra)
    forca_total = (f_ind + f_ma) / 2
    if forca_total > 70: st.success(f"🚀 **COMPRA FORTE ({forca_total:.0f}%)**")
    elif forca_total < 30: st.error(f"📉 **VENDA FORTE ({100-forca_total:.0f}%)**")
    else: st.warning(f"⚖️ **NEUTRO ({forca_total:.0f}%)**")
    
