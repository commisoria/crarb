from flask import Flask, render_template,make_response
import requests
import pandas as pd
import time
import threading

def binance():
    binance_url = "https://api.binance.com/api/v3/ticker/bookTicker"
    response = requests.get(url=binance_url).json()
    binance_prices = [{'symbol': item['symbol'],'bid': item['bidPrice'],'ask': item['askPrice'],
                       'bid_size': item['bidQty'],'ask_size': item['askQty']} for item in response]
    df=pd.DataFrame(binance_prices)
    df['bid'] = pd.to_numeric(df['bid'])
    df['ask'] = pd.to_numeric(df['ask'])
    df['ask_size'] = pd.to_numeric(df['ask_size'])
    df['bid_size'] = pd.to_numeric(df['bid_size'])
    return df

def kucoin():
    kucoin_url = "https://api.kucoin.com/api/v1/market/allTickers"
    kucoin_response = requests.get(url=kucoin_url).json()
    df= [{'symbol': item['symbol'], 'kucoin_price': item['last'], 'kucoin_bid': item['buy'],'kucoin_bid_size': item['bestBidSize'], 'kucoin_ask': item['sell'],'kucoin_ask_size': item['bestAskSize'], 'kucoin_change_rate': item['changeRate'],'kucoin_vol': item['vol']} for item in kucoin_response['data']['ticker']]
    df= pd.DataFrame(df)
    df[['key_string', 'pair_type']] = df['symbol'].str.split('-', expand=True)
    df=df[df['pair_type'] == 'USDT']
    df['symbol']=df['symbol'].str.replace('-','')
    df=df.rename(columns={'kucoin_bid':'bid', 'kucoin_ask':'ask','kucoin_bid_size':'bid_size','kucoin_ask_size':'ask_size'})
    df=df[['symbol','bid','ask','bid_size','ask_size']]
    df['bid'] = pd.to_numeric(df['bid'])
    df['ask'] = pd.to_numeric(df['ask'])
    df['ask_size'] = pd.to_numeric(df['ask_size'])
    df['bid_size'] = pd.to_numeric(df['bid_size'])
    return df

def bitmart():
  symbols_url="https://api-cloud.bitmart.com/spot/v1/symbols"
  symbols_resp=requests.get(symbols_url).json()
  df1=pd.DataFrame(symbols_resp['data']['symbols'])
  df1=df1.rename(columns={0:'symbol',})
  tickers_url = "https://api-cloud.bitmart.com/spot/quotation/v3/tickers"
  tickers_resp = requests.get(tickers_url).json()
  df2=pd.DataFrame(tickers_resp['data'])
  df2=df2.rename(columns={0:'symbol',})
  df= pd.merge(df1, df2, on='symbol')
  df=df[['symbol',8,10,9,11]]
  df=df.rename(columns={10:'ask',8:'bid',9:'ask_size',11:'bid_size'})
  df['symbol']=df['symbol'].str.replace('_','',regex=False)
  df['symbol']=df['symbol'].str.replace('$','',regex=False)
  df = df[df['symbol'].str[-4:] == 'USDT']
  df['ask']=pd.to_numeric(df['ask'])
  df['bid']=pd.to_numeric(df['bid'])
  df['ask_size'] = pd.to_numeric(df['ask_size'],errors='coerce')
  df['bid_size'] = pd.to_numeric(df['bid_size'],errors='coerce')
  return df

def bitget():
    url = "https://api.bitget.com/api/v2/spot/market/tickers"
    response = requests.get(url)
    data = response.json()["data"]
    df = pd.DataFrame(data)
    df=df[['symbol','lastPr','bidPr','askPr','bidSz','askSz','change24h']]
    df['bidPr'] = pd.to_numeric(df['bidPr'])
    df['askPr']=pd.to_numeric(df['askPr'])
    df['bidSz'] = pd.to_numeric(df['bidSz'])
    df['askSz'] = pd.to_numeric(df['askSz'])
    df['key_string'] = df['symbol'].str.replace('USDT','',regex=False)
    df=df.rename(columns={'lastPr':'price', 'bidPr': 'bid', 'askPr': 'ask','bidSz':'bid_size', 'askSz':'ask_size'})
    df=df[['symbol','bid','ask','bid_size','ask_size']]
    return df

def bybit():
    url = 'https://api.bybit.com/v5/market/tickers?category=spot'
    try:
        # Fetch the data
        response = requests.get(url)
        response.raise_for_status()  # Raise error if request fails
        data = response.json()

        # Filter USDT pairs and get their relevant details
        usdt_pairs = {
            ticker['symbol']: {
                'lastPrice': ticker['lastPrice'],
                'bidPrice': ticker['bid1Price'],
                'askPrice': ticker['ask1Price'],
                'bidSize': ticker['bid1Size'],
                'askSize': ticker['ask1Size']
            }
            for ticker in data['result']['list'] if ticker['symbol'].endswith('USDT')
        }

        # Create a DataFrame and rename columns
        df = pd.DataFrame.from_dict(usdt_pairs, orient='index').reset_index()
        df = df.rename(columns={'index': 'symbol', 'lastPrice': 'price',
                                'bidPrice': 'bid', 'askPrice': 'ask',
                                'bidSize': 'bid_size', 'askSize': 'ask_size'})

        # Convert bid and ask prices to numeric values
        df[['bid', 'ask', 'bid_size', 'ask_size']] = df[['bid', 'ask', 'bid_size', 'ask_size']].apply(pd.to_numeric)

        # Extract coin name from symbol
        df['key_string'] = df['symbol'].str.replace('USDT', '', regex=False)

        # Organize final DataFrame
        df = df[['symbol','bid', 'ask','bid_size', 'ask_size']]
        return df
    except Exception as e:
        return e


def huobi():
  url = "https://api.huobi.pro/market/tickers"
  response = requests.get(url)
  data = response.json()

  # Parse and load into DataFrame
  if 'data' in data:
      df = pd.DataFrame(data['data'])
      df = df[['symbol', 'ask', 'bid', 'askSize', 'bidSize']]  # Select common fields
      for col in df.columns:
          if df[col].dtype == object or df[col].dtype.name == 'string':
              df[col] = df[col].map(lambda v: v.upper() if isinstance(v, str) else v)
      #df=df.applymap(lambda v: v.upper() if isinstance(v, str) else v)
      df=df.rename(columns={'bidSize':'bid_size', 'askSize':'ask_size'})
      df=df[['symbol','bid','ask','bid_size','ask_size']]
      df['bid'] = pd.to_numeric(df['bid'])
      df['ask'] = pd.to_numeric(df['ask'])
      df['ask_size'] = pd.to_numeric(df['ask_size'])
      df['bid_size'] = pd.to_numeric(df['bid_size'])
      return df
  else:
      return None
def okx():
    instruments_url = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"
    instruments = requests.get(instruments_url).json()['data']
    usdt_pairs = [item['instId'] for item in instruments if item['quoteCcy'] == 'USDT']
    tickers_url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    tickers = requests.get(tickers_url).json()['data']
    records = []
    for t in tickers:
      if t['instId'] in usdt_pairs:
          records.append({
              'symbol': t['instId'],
              'bid': float(t['bidPx']),
              'ask': float(t['askPx']),
              'bid_size': float(t['bidSz']),
              'ask_size': float(t['askSz']),})

    # Step 5: Create DataFrame
    df = pd.DataFrame(records)
    df = df[df['symbol'].str[-4:] == 'USDT']
    df['symbol']=df['symbol'].str.replace('-','')
    df['bid'] = pd.to_numeric(df['bid'])
    df['ask'] = pd.to_numeric(df['ask'])
    df['ask_size'] = pd.to_numeric(df['ask_size'])
    df['bid_size'] = pd.to_numeric(df['bid_size'])
    return df

def mexc():
  url = "https://api.mexc.com/api/v3/ticker/bookTicker"
  response = requests.get(url)
  data = response.json()
  df = pd.DataFrame(data)
  df = df[['symbol', 'askPrice', 'bidPrice', 'askQty', 'bidQty']]
  df.columns = ['symbol', 'ask', 'bid', 'ask_size', 'bid_size']
  df = df[df['symbol'].str[-4:] == 'USDT']
  df['bid'] = pd.to_numeric(df['bid'])
  df['ask'] = pd.to_numeric(df['ask'])
  df['ask_size'] = pd.to_numeric(df['ask_size'])
  df['bid_size'] = pd.to_numeric(df['bid_size'])
  return df

def module1(capital):
    # exchange definitions
    bitgetx=bitget()
    bybitx=bybit()
    kucoinx=kucoin()
    mexcx=mexc()
    binancex = binance()
    huobix=huobi()
    okxx=okx()
    bitmartx=bitmart()
    bitget_bybit=pd.merge(bitgetx,bybitx,on='symbol',suffixes=('_a','_b'))
    bitget_bybit['Cross'] = 'bitget_bybit'
    bitget_kucoin=pd.merge(bitgetx,kucoinx,on='symbol',suffixes=('_a','_b'))
    bitget_kucoin['Cross'] = 'bitget_kucoin'
    bitget_bitmart=pd.merge(bitgetx,bitmartx,on='symbol',suffixes=('_a','_b'))
    bitget_bitmart['Cross'] = 'bitget_bitmart'
    bitget_huobi= pd.merge(bitgetx,huobix,on='symbol', suffixes=('_a', '_b'))
    bitget_huobi['Cross'] = 'bitget_huobi'
    bitget_okx= pd.merge(bitgetx,okxx, on='symbol', suffixes=('_a', '_b'))
    bitget_okx['Cross'] = 'bitget_okx'
    bitget_mexc=pd.merge(bitgetx,mexcx, on='symbol', suffixes=('_a', '_b'))
    bitget_mexc['Cross'] = 'bitget_mexc'
    bitget_binance= pd.merge(bitgetx,binancex, on='symbol', suffixes=('_a', '_b'))
    bitget_binance['Cross'] = 'bitget_binance'
    bybit_kucoin = pd.merge(bybitx,kucoinx, on='symbol', suffixes=('_a', '_b'))
    bybit_kucoin['Cross'] = 'bybit_kucoin'
    bybit_bitmart= pd.merge(bybitx,bitmartx, on='symbol', suffixes=('_a', '_b'))
    bybit_bitmart['Cross'] = 'bybit_bitmart'
    bybit_huobi= pd.merge(bybitx,huobix, on='symbol', suffixes=('_a', '_b'))
    bybit_huobi['Cross'] = 'bybit_huobi'
    bybit_okx=pd.merge(bybitx,okxx, on='symbol', suffixes=('_a', '_b'))
    bybit_okx['Cross'] = 'bybit_okx'
    bybit_mexc = pd.merge(bybitx,mexcx, on='symbol', suffixes=('_a', '_b'))
    bybit_mexc['Cross'] = 'bybit_mexc'
    bybit_binance = pd.merge(bybitx,binancex, on='symbol', suffixes=('_a', '_b'))
    bybit_binance['Cross'] = 'bybit_binance'
    kucoin_bitmart= pd.merge(kucoinx,bitmartx, on='symbol', suffixes=('_a', '_b'))
    kucoin_bitmart['Cross'] = 'kucoin_bitmart'
    kucoin_huobi= pd.merge(kucoinx,huobix, on='symbol', suffixes=('_a', '_b'))
    kucoin_huobi['Cross'] = 'kucoin_huobi'
    kucoin_okx =pd.merge(kucoinx,okxx, on='symbol', suffixes=('_a', '_b'))
    kucoin_okx['Cross'] = 'kucoin_okx'
    kucoin_mexc = pd.merge(kucoinx,mexcx, on='symbol', suffixes=('_a', '_b'))
    kucoin_mexc['Cross'] = 'kucoin_mexc'
    kucoin_binance = pd.merge(kucoinx,binancex, on='symbol', suffixes=('_a', '_b'))
    kucoin_binance['Cross'] = 'kucoin_binance'
    bitmart_huobi= pd.merge(bitmartx,huobix, on='symbol', suffixes=('_a', '_b'))
    bitmart_huobi['Cross'] = 'bitmart_huobi'
    bitmart_okx = pd.merge(bitmartx,okxx, on='symbol', suffixes=('_a', '_b'))
    bitmart_okx['Cross'] = 'bitmart_okx'
    bitmart_mexc= pd.merge(bitmartx,mexcx, on='symbol', suffixes=('_a', '_b'))
    bitmart_mexc['Cross'] = 'bitmart_mexc'
    bitmart_binance= pd.merge(bitmartx,binancex, on='symbol', suffixes=('_a', '_b'))
    bitmart_binance['Cross'] = 'bitmart_binance'
    huobi_okx=pd.merge(huobix,okxx, on='symbol', suffixes=('_a', '_b'))
    huobi_okx['Cross'] = 'huobi_okx'
    huobi_mexc= pd.merge(huobix,mexcx, on='symbol', suffixes=('_a', '_b'))
    huobi_mexc['Cross'] = 'huobi_mexc'
    huobi_binance= pd.merge(huobix,binancex, on='symbol', suffixes=('_a', '_b'))
    huobi_binance['Cross'] = 'huobi_binance'
    okx_mexc= pd.merge(okxx,mexcx, on='symbol', suffixes=('_a', '_b'))
    okx_mexc['Cross'] = 'okx_mexc'
    okx_binance=pd.merge(okxx,binancex, on='symbol', suffixes=('_a', '_b'))
    okx_binance['Cross'] = 'okx_binance'
    mexc_binance = pd.merge(mexcx, binancex, on='symbol', suffixes=('_a', '_b'))
    mexc_binance['Cross'] = 'mexc_binance'
    combined_df = pd.concat([bitget_bybit,bitget_kucoin,bitget_bitmart,bitget_huobi,bitget_okx,bitget_mexc,
    bitget_binance,bybit_kucoin,bybit_bitmart,bybit_huobi,bybit_okx,bybit_mexc,bybit_binance,kucoin_bitmart,kucoin_huobi,
    kucoin_okx,kucoin_mexc,kucoin_binance,bitmart_huobi,bitmart_okx,bitmart_mexc,bitmart_okx,huobi_okx,huobi_mexc,huobi_binance,
    okx_mexc,okx_binance,mexc_binance], ignore_index=True)
    # Last analysis
    combined_df['spread_a']=((combined_df['ask_a']-combined_df['bid_a']).abs())/combined_df['bid_a']
    combined_df['spread_b'] =((combined_df['bid_a'] - combined_df['bid_b']).abs())/combined_df['bid_b']
    combined_df['diff_1'] = combined_df['ask_a'] - combined_df['ask_b']
    combined_df['diff_2'] = combined_df['bid_a'] - combined_df['bid_b']
    combined_df['multiply']=combined_df['diff_1']*combined_df['diff_2']
    combined_df=combined_df[(combined_df['multiply']>0)]
    combined_df['amount (for 1000 $)']=capital/combined_df['bid_a']
    combined_df['gross_profit']=combined_df['amount (for 1000 $)']*combined_df['diff_1']
    combined_df['abs_gross_profit']=combined_df['gross_profit'].abs()
    combined_df=combined_df[(combined_df['abs_gross_profit']>capital*0.001) & (combined_df['abs_gross_profit']<capital*0.1)]
    combined_df['askvol_a']=combined_df['ask_a']*combined_df['ask_size_a']
    combined_df['bidvol_a'] =combined_df['bid_a'] * combined_df['bid_size_a']
    combined_df['askvol_b'] = combined_df['ask_b'] * combined_df['ask_size_b']
    combined_df['bidvol_b'] = combined_df['bid_b'] * combined_df['bid_size_b']
    combined_df['total_size']=combined_df['askvol_a']+combined_df['bidvol_a']+combined_df['askvol_b']+combined_df['bidvol_b']
    combined_df['total_spread']=combined_df['spread_a']+combined_df['spread_b']
    combined_df = combined_df[((combined_df['bidvol_a']>=capital*0.2) & (combined_df['askvol_b']>=capital*0.2)) | ((combined_df['bidvol_b']>=capital*0.2) & (combined_df['askvol_a']>=capital*0.2))]
    combined_df['p1']=(combined_df['bid_a']-combined_df['ask_b'])*combined_df['amount (for 1000 $)']
    combined_df['p2'] = (combined_df['bid_b'] - combined_df['ask_a']) * combined_df['amount (for 1000 $)']
    combined_df=combined_df[(combined_df['p1']>0) | (combined_df['p2']>0)]
    combined_df = combined_df[['Cross', 'symbol','bid_a','ask_a','bid_b','ask_b','total_spread','total_size','gross_profit']]
    combined_df=combined_df.sort_values(by=['gross_profit'], ascending=False)
    return combined_df

pd.options.display.float_format = '{:,.6f}'.format
combined_df = module1(capital=1000)

app = Flask(__name__)

@app.route('/')
def show_table():
    return render_template("index.html")

@app.route('/table')
def table_only():
    global combined_df
    combined_df = module1(capital=1000)  # Refresh data
    table_html = combined_df.to_html(
        classes='table table-bordered display nowrap',
        index=False,
        table_id="data-table"
    )
    response = make_response(table_html)
    response.headers['Cache-Control'] = 'no-store'  # Prevent browser from caching
    return response

if __name__ == '__main__':
    app.run(debug=True)