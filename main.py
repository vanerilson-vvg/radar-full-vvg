    # --- CÁLCULO DE FORÇA CORRIGIDO ---
    c_ma = sum(1 for m in ma1 if "COMPRA" in m[1])
    total_ma = len(ma1)
    
    # Se houver mais venda que compra, mostramos a força de VENDA
    if c_ma <= (total_ma / 2):
        f_venda = ((total_ma - c_ma) / total_ma) * 100
        status_ma = "🔴" if f_venda > 50 else "⚪"
        texto_forca = f"{status_ma} **FORÇA MÉDIAS (VENDA):** {f_venda:.0f}%"
        valor_progresso = f_venda / 100
    else:
        f_compra = (c_ma / total_ma) * 100
        status_ma = "🟢"
        texto_forca = f"{status_ma} **FORÇA MÉDIAS (COMPRA):** {f_compra:.0f}%"
        valor_progresso = f_compra / 100

    st.write(texto_forca)
    st.progress(valor_progresso)
