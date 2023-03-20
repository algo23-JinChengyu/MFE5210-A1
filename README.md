# MFE5210-A1
# main.py为主程序，运行该文件可以执行：
#    1.dominant_contract()函数获取主力合约，计算主力合约复权因子，plotprice()函数绘制主力合约复权收盘价曲线
#    2.macd_ddi_signal()函数获取交易信号文件
#    3.backtrade()函数使用主力合约价格数据和交易信号文件进行交易回测

# module文件内包含以下三个.py文件

# getcontract.py文件负责从原始合约数据中选取主力合约数据，计算主力合约切换时的复权因子，并绘制主力合约复权收盘价曲线
# tradingsignal.py文件负责用主力合约数据按照交易思路计算交易信号
# backtest.py文件包含一个broker类，可以使用主力合约数据与交易信号来进行交易回测，绘制资金曲线并计算相关指标
