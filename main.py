from module.getcontract import *
from module.tradingsignal import *
from module.backtest import *
import warnings
warnings.filterwarnings("ignore")

# 获取主力合约量价数据
contract_data = dominant_contract()
contract_data.to_csv(r"./主力合约数据.csv",index=False)

# 绘制主力合约复权收盘价曲线
plotPrice(contract_data)

# 获取交易信号
signal_data = macd_ddi_signal(contract_data)

# 交易回测
def backtrade(data,signal,t,k1,k2):
    """
    data:DataFrame : 主力合约量价数据
    signal:DataFrame : 交易信号数据
    t:int : ATR周期,ATR用于判断止损
    k1:float : 多头持仓止损容忍度
    k2:float : 空头持仓止损容忍度
    """
    model = broker() 
    model.trade(data,signal,t,k1,k2)
    model.showindicator() # 打印年化收益，波动率，夏普比率，最大回撤，最大回撤期，卡玛比率
    model.plot_capital_line() # 绘制资金曲线和复权收盘价曲线

backtrade(contract_data,signal_data,45,1,2)
