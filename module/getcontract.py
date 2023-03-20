import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei']

def dominant_contract(): # 获取主力合约并计算复权因子
    # 导入数据
    price_data = pd.read_excel(r"./菜籽油.xlsx")
    price_data["InstrumentID"] = price_data["InstrumentID"].apply(lambda x : x.strip())

    # 选出主力合约，并计算复权因子
    contract = price_data.groupby("ExchTime").apply(lambda x: x[x['Volume'] == x['Volume'].max()])[["InstrumentID","ExchTime"]].reset_index(drop=True)
    contract["tradeID"] = contract["InstrumentID"]
    contract["adjustor"] = 1
    for idx in contract.index[5:]:
        if contract.loc[idx-4,"InstrumentID"] != contract.loc[idx-5,"InstrumentID"]: # 最大持仓合约发生改变
            if (contract.loc[idx-4,"InstrumentID"] == contract.loc[idx-3,"InstrumentID"]) &\
                (contract.loc[idx-4,"InstrumentID"] == contract.loc[idx-2,"InstrumentID"]): # 并且持续三天，则进行主力合约切换
                contract.loc[idx,"tradeID"] = contract.loc[idx-2,"InstrumentID"]

                old_contract = contract.loc[idx-1,"tradeID"]
                new_contract = contract.loc[idx,"tradeID"]
                old_ExchTime = contract.loc[idx-1,"ExchTime"]

                old_contract_yesterday_idx = price_data[(price_data["ExchTime"] == old_ExchTime)&(price_data["InstrumentID"] == old_contract)].index[0]
                new_contract_yesterday_idx = price_data[(price_data["ExchTime"] == old_ExchTime)&(price_data["InstrumentID"] == new_contract)].index[0]
                
                contract.loc[idx,"adjustor"] = price_data.loc[old_contract_yesterday_idx,"ClosePrice"]/price_data.loc[new_contract_yesterday_idx,"ClosePrice"]
        else:
            contract.loc[idx,"tradeID"] = contract.loc[idx-1,"tradeID"]

    contract_data = pd.merge(price_data, contract[["ExchTime","tradeID","adjustor"]].rename(columns={"tradeID":"InstrumentID"}), on = ["InstrumentID","ExchTime"], how = "right")
    contract_data["adjustor"] = contract_data["adjustor"].cumprod()
    return contract_data

def plotPrice(data): # 复权收盘价曲线
    plt.plot(data["ExchTime"],data["ClosePrice"] * data["adjustor"])
    plt.title("菜籽油主力合约复权收盘价:(元/吨)")
    plt.show()