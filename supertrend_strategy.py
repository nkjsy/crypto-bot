import pandas_ta as ta


def supertrend_tv(df, atr_period, multiplier):  
    df_supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=atr_period, atr_length=atr_period, multiplier=multiplier, atr_mamode='rma', offset=1)
    direction_col = f"SUPERTd_{atr_period}_{multiplier}"
    df_final = df.join(df_supertrend)
    direction = ta.consecutive_streak(df_final[direction_col])
    df_final['signal'] = direction
    # print(df_final.tail(10))
    return df_final