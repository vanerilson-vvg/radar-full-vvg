import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ATUALIZAÇÃO ULTRA RÁPIDA (2 SEGUNDOS)
st.set_page_config(page_title="VVG Terminal M5/M15", layout="wide")
st_autorefresh(interval=2000, key="vvg_v16_m5_m15")

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
    # Buscamos range de 5 dias para garantir dados para médias longas em M15
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval={intervalo}&range=5d"
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
    s['EMA 9'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=9).iloc[-1] else "🔴 VENDA"
    s['EMA 21'] = "🟢 COMPRA" if c.iloc[-1] > ta.ema(c, length=21).iloc[-1] else "🔴 VENDA"
    rsi = ta.rsi(c, length=14).iloc[-1]
    s['RSI (14)'] = "🟢 COMPRA" if rsi < 45 else ("🔴 VENDA" if rsi > 55 else "⚪ NEUTRO")
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

def exibir_barra_forca(lista_sinais, titulo):
    if isinstance(lista_sinais, dict):
        votos_compra = sum(1 for v in lista_sinais.values() if "COMPRA" in v)
        total = len(lista_sinais)
    else:
        votos_compra = sum(1 for m in lista_sinais if "COMPRA" in m[1])
        total = len(lista_sinais)

    if votos_compra > (total / 2):
        forca = (votos_compra / total) * 100
        st.write(f"🟢 **{titulo} (COMPRA):** {forca:.0f}%")
        st.progress(forca/100)
    elif votos_compra < (total / 2):
        forca = ((total - votos_compra) / total) * 100
        st.write(f"🔴 **{titulo} (VENDA):** {forca:.0f}%")
        st.progress(forca/100)
    else:
        st.write(f"⚪ **{titulo} (NEUTRO):** 50%")
        st.progress(0.5)

# --- EXECUÇÃO (M5 e M15) ---
df5, preco, anterior = buscar_dados_completos("5m")
df15, _, _ = buscar_dados_completos("15m")

if df5 is not None:
    # Ajuste MT5 (4 pontos)
    preco_reajustado = preco - 0.00040 
    variacao = preco - anterior
    pips = variacao * 10000
    cor_classe = "price-main" if variacao >= 0 else "price-down"

    st.markdown(f"### 🖥️ TERMINAL VVG | EUR/USD (M5)")
    st.markdown(f'<p class="{cor_classe}">{preco:.5f} <span style="font-size:16px;">({pips:.1f} Pips)</span></p>', unsafe_allow_html=True)
    st.markdown(f'<p class="price-mt5">MT5: {preco_reajustado:.5f}</p>', unsafe_allow_html=True)
    st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")

    st.markdown("---")
    
    # BLOCO 1: INDICADORES TÉCNICOS
    st.markdown("### 📊 INDICADORES TÉCNICOS")
    ind5, ind15 = calcular_sinais(df5), calcular_sinais(df15)
    st.table(pd.DataFrame([[k, ind5[k], ind15.get(k, "⚪ ---")] for k in ind5.keys()], columns=["INDICADOR", "M5", "M15"]))
    exibir_barra_forca(ind5, "FORÇA INDICADORES (M5)")
    
    st.markdown("---")

    # BLOCO 2: MÉDIAS MÓVEIS
    st.markdown("### 📈 MÉDIAS MÓVEIS")
    ma5, ma15 = painel_medias(df5), painel_medias(df15)
    col1, col2 = st.columns(2)
    with col1: st.write("⏱️ **M5**"); st.table(pd.DataFrame(ma5, columns=["PERÍODO", "SINAL"]))
    with col2: st.write("⏱️ **M15**"); st.table(pd.DataFrame(ma15, columns=["PERÍODO", "SINAL"]))
    exibir_barra_forca(ma5, "FORÇA MÉDIAS (M5)")

    st.markdown("---")

    # BLOCO 3: VEREDITO FINAL (Baseado no M5 com confirmação visual do M15)
    c_total = sum(1 for v in ind5.values() if "COMPRA" in v) + sum(1 for m in ma5 if "COMPRA" in m[1])
    total_itens = len(ind5) + len(ma5)
    forca_final = (c_total / total_itens) * 100

    if forca_final > 70: st.success(f"🚀 **M5: COMPRA FORTE ({forca_final:.0f}%)**")
    elif forca_final < 30: st.error(f"📉 **M5: VENDA FORTE ({100-forca_final:.0f}%)**")
    else: st.warning(f"⚖️ **M5: NEUTRO ({forca_final:.0f}%)**")
    
