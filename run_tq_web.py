# coding: utf-8
"""
天勤开始收费，我继续来维护这个脚本
=================================================
"""
import os
import json
import pandas as pd
import czsc
from datetime import datetime, timedelta
from flask import Flask, request, make_response, jsonify
from tqsdk import TqApi, TqAuth, TqBacktest

# 定义回测日期范围
Backtest_Date = TqBacktest(start_dt=datetime(2024, 1, 1), end_dt=datetime(2024, 12, 31))

base_path = os.path.split(os.path.realpath(__file__))[0]
web_path = os.path.join(base_path, 'web')
app = Flask(__name__, static_folder=web_path)

# 初始化TqApi
# 注意：如果是实盘，请使用 api = TqApi(auth=TqAuth("账户", "密码"))
# 如果是回测，使用下面的方式
#api = TqApi(backtest=Backtest_Date,
#            web_gui=True,
#            auth=TqAuth("**********", "Lucky9129"))    # 修改为你的账户和密码
api = TqApi(auth=TqAuth("1590100****", "Lucky9129"))    # 修改为你的账户和密码

def format_kline(kline):
    """格式化K线"""
    def __convert_time(t):
        try:
            dt = datetime.fromtimestamp(t/1000000000, tz=datetime.timezone.utc)
            dt = dt + timedelta(hours=8)    # 中国默认时区
            return dt
        except:
            return ""

    kline['dt'] = kline['datetime'].apply(__convert_time)
    kline['vol'] = kline['volume']
    columns = ['symbol', 'dt', 'open', 'close', 'high', 'low', 'vol']
    df = kline[columns]
    df = df.dropna(axis=0)
    df.drop_duplicates(subset=['dt'], inplace=True)
    df.sort_values('dt', inplace=True, ascending=True)
    df.reset_index(drop=True, inplace=True)
    return df


def get_kline(symbol="SHFE.cu2601", freq='1min', k_count=3000):
    """获取K线"""
    freq_map = {'1min': 60, '5min': 300, '15min': 900, '30min': 1800,
                '60min': 3600, 'D': 3600*24, 'W': 86400*7}
    df = api.get_kline_serial(symbol, duration_seconds=freq_map[freq], data_length=k_count)
    df = format_kline(df)
    return df


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.route('/kline', methods=['POST', 'GET'])
def kline():
    if request.method == "POST":
        data = json.loads(request.get_data(as_text=True))
    elif request.method == "GET":
        data = request.args
    else:
        raise ValueError

    ts_code = data.get('ts_code')
    freq = data.get('freq')
    k = get_kline(symbol=ts_code, freq=freq, k_count=5000)
    
    # 修复czsc库使用方式
    # 检查czsc版本并使用兼容的方式
    try:
        # 尝试使用czsc的最新版本API
        from czsc.analyze import CZSC
        ka = CZSC(k)
        # 提取需要的数据列
        k['fx_mark'] = ''  # 分型标记
        k['fx'] = ''  # 分型
        k['bi'] = ''  # 笔
        k['xd'] = ''  # 线段
    except:
        # 如果导入失败，使用基本的数据格式
        k['fx_mark'] = ''
        k['fx'] = ''
        k['bi'] = ''
        k['xd'] = ''

    k = k.fillna("")
    k.loc[:, "dt"] = k.dt.apply(str)  # 修复变量引用错误
    columns = ["dt", "open", "close", "low", "high", "vol", 'fx_mark', 'fx', 'bi', 'xd']
    res = make_response(jsonify({'kdata': k[columns].values.tolist()}))
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Method'] = '*'
    res.headers['Access-Control-Allow-Headers'] = '*'
    return res


if __name__ == '__main__':
    app.run(port=8005, debug=True)



