# 交易回测模块
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class broker:

    transaction_fees = 0.00035 # 手续费与滑点

    def __init__(self,cash=1000000):
        self.cash = cash # 现金
        self.value_record = [] # 记录账户每日价值
        self.trading_record = [] # 交易记录日期，交易吨数，交易价格
        self.position = 0 # 仓位，绝对值表示手数，符号表示多空方向

        self.minNumber = 5 # 初始每手5吨，切换后为每手10吨

    def trade_log(self,dt,num,prc): # 记录交易
        self.trading_record.append([dt,num,prc])

    def order(self,date,number,price,fees=1): # 下单函数
        self.cash = self.cash - number * price*(1 + fees*broker.transaction_fees) * self.minNumber 
        self.position += number # 更新仓位
        self.trade_log(date,number * self.minNumber,price)

    def calc_atr(self,data,t): # 计算ATR,用于计算止损线
        df = data.copy()
        df["adjusted_high"] = df["HighPrice"] * df["adjustor"]
        df["adjusted_low"] = df["LowPrice"] * df["adjustor"]
        df["adjusted_last_close"] = (df["ClosePrice"] * df["adjustor"]).shift(1)
        df["tr"] = df.apply(lambda x: max(x["adjusted_high"],x["adjusted_last_close"]) - min(x["adjusted_low"],x["adjusted_last_close"]),axis=1)
        df["atr"] = df["tr"].rolling(t).mean().fillna(np.inf)
        data["atr"] = df["atr"]

    def check_stop_loss(self,dt,data,idx,k1,k2): # 检查止损函数
        last_dt = self.trading_record[-1][0] # 上一个开仓日期
        last_dt_idx = data[data["ExchTime"] == last_dt].index[0]
        if self.position > 0:
            limit = (data["HighPrice"] * data["adjustor"])[last_dt_idx:idx-1].max() - k1 * data.loc[idx-1,"atr"]
            if data.loc[idx-1,"ClosePrice"] * data.loc[idx-1,"adjustor"] <= limit:
                self.order(dt,-self.position,data.loc[idx,"OpenPrice"],0) # 清仓
        if self.position < 0:
            limit = (data["LowPrice"] * data["adjustor"])[last_dt_idx:idx-1].min() + k2 * data.loc[idx-1,"atr"]
            if data.loc[idx-1,"ClosePrice"] * data.loc[idx-1,"adjustor"] >= limit:
                self.order(dt,-self.position,data.loc[idx,"OpenPrice"],0) # 清仓

    def trade(self,data,signal_data,t=45,k1=1,k2=2): 
        self.calc_atr(data,t) # 计算ATR，用于计算止损线
    
        for idx in data.index: 
            trade_date = data.loc[idx,"ExchTime"] 
            open_price = data.loc[idx,"OpenPrice"]
            close_price = data.loc[idx,"ClosePrice"]

            if self.position != 0: # 若有持仓则检查是否需要止损
                self.check_stop_loss(trade_date,data,idx,k1,k2) # 检验昨日是否触发止损信号，若触发则当日开盘清仓

            if signal_data.loc[idx,"signal"] == 1: # 看多信号
                # 检查是否有持仓
                if self.position == 0: # 没有持仓，以开盘价进行买入
                    long_number = self.cash//(open_price * (1 + broker.transaction_fees) * self.minNumber) # 计算可买手数
                    self.order(trade_date,long_number,open_price)
                if self.position > 0: # 有多头持仓，不进行操作
                    pass
                if self.position < 0: # 有空头持仓，先平仓，再开多头仓
                    self.order(trade_date,-self.position,open_price,0)
                    long_number = self.cash//(open_price * (1 + broker.transaction_fees) * self.minNumber) # 计算可买手数
                    self.order(trade_date,long_number,open_price)

            if signal_data.loc[idx,"signal"] == -1: # 看空信号
                # 检查是否有持仓
                if self.position == 0: # 没有持仓，以开盘价进行做空
                    short_number = self.cash//(open_price * (1 + broker.transaction_fees) * self.minNumber) # 计算可买手数
                    self.order(trade_date,-short_number,open_price)
                if self.position < 0: # 有多头持仓，不进行操作
                    pass
                if self.position > 0: # 有多头持仓，先平仓，再开空头仓
                    self.order(trade_date,-self.position,open_price,0)
                    short_number = self.cash//(open_price * (1 + broker.transaction_fees) * self.minNumber) # 计算可买手数
                    self.order(trade_date,-short_number,open_price)
            
            # 检查是否需要切换主力合约
            if self.position == 0: # 若无持仓则不用操作
                pass
            elif idx != data.index[-1]:
                if data.loc[idx,"InstrumentID"] != data.loc[idx+1,"InstrumentID"]: # 主力合约切换
                    if self.minNumber == 5:
                        if data.loc[idx+1,"InstrumentID"].startswith("OI"):
                            self.minNumber = 10 # 合约乘数由5变为10
                            self.position = self.position/2
                    direction = np.sign(self.position)
                    self.order(trade_date,-self.position,close_price,0) # 以收盘价清仓旧主力合约
                    new_close_price = int(data.loc[idx,"adjustor"] / data.loc[idx+1,"adjustor"] * close_price) # 由复权因子和旧主力收盘价计算新主力收盘价
                    new_number = self.cash//(new_close_price * (1 + broker.transaction_fees) * self.minNumber)
                    self.order(trade_date,new_number * direction, new_close_price) # 以新主力合约收盘价建仓
                    close_price = new_close_price

            # 记录收盘时账户价值
            self.value_record.append(self.cash + self.position * close_price * self.minNumber)
        
        # 记入日期和复权价格
        self.ExchTime = data["ExchTime"].tolist() 
        self.price = data["ClosePrice"] * data["adjustor"] # 复权价格序列
    
    def plot_capital_line(self): # 呈现资金曲线
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        l1, = ax1.plot(self.ExchTime,self.value_record,color = 'black')
        l2, = ax2.plot(self.ExchTime,self.price.tolist(),color = 'red')
        plt.legend(handles = [l1,l2], labels = ['策略资金','主力合约复权收盘价'], loc="upper center")
        plt.title("菜籽油期货趋势交易策略")
        plt.show()

    def showindicator(self):
        df = pd.DataFrame({'Date': self.ExchTime, 'Fund': self.value_record})
        df.set_index('Date', inplace=True)

        # 计算年化收益率
        n = len(df)
        returns = df['Fund'].pct_change().dropna()
        annual_return = ((1 + returns).prod()) ** (252 / n) - 1

        # 计算年化波动率
        annual_volatility = returns.std() * np.sqrt(252)

        # 计算夏普比率
        sharpe_ratio = annual_return / annual_volatility

        # 计算最大回撤和最大回撤期
        drawdowns = (df['Fund'] / df['Fund'].cummax() - 1).reset_index(drop=True)
        max_drawdown = drawdowns.min()

        drawdowns = drawdowns.reset_index()
        max_drawdown_days = drawdowns[drawdowns["Fund"] == 0]["index"].diff(1).max()

        # 计算Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown)

        print("# 年化收益率: {:.4f}".format(annual_return))
        print("# 年化波动率: {:.4f}".format(annual_volatility))
        print("# 夏普比率: {:.4f}".format(sharpe_ratio))
        print("# 最大回撤: {:.4f}".format(max_drawdown))
        print("# 最大回撤时长: {}".format(int(max_drawdown_days)))
        print("# Calmar比率: {:.4f}".format(calmar_ratio))



    
            

            
                    
                    






