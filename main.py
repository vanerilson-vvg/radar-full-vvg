    # Bollinger Bands (Cálculo robusto)
    bb = ta.bbands(c, length=20)
    if bb is not None:
        # Usamos o índice [-1] da primeira e última coluna para evitar erro de nome
        col_baixa = bb.iloc[:, 0] # Banda Inferior
        col_alta = bb.iloc[:, 2]  # Banda Superior
        if c.iloc[-1] < col_baixa.iloc[-1]:
            s['Bollinger'] = "🟢 COMPRA"
        elif c.iloc[-1] > col_alta.iloc[-1]:
            s['Bollinger'] = "🔴 VENDA"
        else:
            s['Bollinger'] = "⚪ NEUTRO"
    else:
        s['Bollinger'] = "⚪ ---"
