import numpy as np

# 信号函数
def macd_ddi_signal(data,n1=13,n2=26,n3=8,m1=13,m2=5,m3=5):
        # data:主力合约数据
        # n1,n2,n3为MACD参数
        # m1,m2,m3为DDI参数

    df = data[["ExchTime","HighPrice","LowPrice","ClosePrice","adjustor"]]

    ####DDI
    df["high"] = df["HighPrice"] * df["adjustor"]
    df["low"] = df["LowPrice"] * df["adjustor"]

    change = np.maximum(abs(df["high"]-df["high"].shift(1)),abs(df["low"]-df["low"].shift(1)))

    dmz = change.copy()
    dmf = change.copy()
    dmz[(df["high"]+df["low"]) < (df["high"]+df["low"]).shift(1)] = 0
    dmf[(df["high"]+df["low"]) > (df["high"]+df["low"]).shift(1)] = 0

    diz = dmz.rolling(m1).sum()/(dmz.rolling(m1).sum()+dmf.rolling(m1).sum())
    dif = dmf.rolling(m1).sum()/(dmz.rolling(m1).sum()+dmf.rolling(m1).sum())

    df["ddi"] = diz-dif
    df["addi"] = df["ddi"].ewm(span=m2,min_periods=m2).mean()
    df["ad"] = df["addi"].rolling(m3).mean()

    ####MACD（使用SMA计算）
    df["price"] = df["ClosePrice"] * df["adjustor"]
    df["dif"] = df["price"].rolling(n1).mean() - df["price"].rolling(n2).mean()
    df["dea"] = df["dif"].rolling(n3).mean()

    #####交易信号，1为看多，-1为看空
    signal = np.zeros(len(df))
    signal[(df["dif"].shift(1) > df["dea"].shift(1))&(df["dif"].shift(2) <= df["dea"].shift(2))&\
            (df["ddi"].shift(1)>0)&(df["addi"].shift(1)>df["ad"].shift(1))] = 1
    signal[(df["dif"].shift(1) < df["dea"].shift(1))&(df["dif"].shift(2) >= df["dea"].shift(2))&\
            (df["ddi"].shift(1)<0)&(df["addi"].shift(1)<df["ad"].shift(1))] = -1

    df["signal"] = signal
    return df[["ExchTime","signal"]]






