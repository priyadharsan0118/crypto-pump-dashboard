import streamlit as st
import pandas as pd
import requests
import numpy as np
import time
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# === Utility Functions ===def get_binance_top_gainers():def get_binance_top_gainers():
    import streamlit as st
    import requests
    import pandas as pd

    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        res = requests.get(url).json()
        if not isinstance(res, list):
            st.error("Binance API did not return expected data.")
            return pd.DataFrame()

        df = pd.DataFrame(res)
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['volume'] = df['quoteVolume'].astype(float)
        top = df.sort_values(by='priceChangePercent', ascending=False)
        return top[['symbol', 'priceChangePercent', 'volume']].head(20)

    except Exception as e:
        st.error(f"Failed to fetch Binance data: {e}")
        return pd.DataFrame()



def get_klines(symbol, interval='1h', limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','qav','num_trades','taker_base_vol','taker_quote_vol','ignore'])
        df['close'] = df['close'].astype(float)
        return df
    except:
        return None

def analyze_technical_signals(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return None

    rsi = RSIIndicator(close=df['close']).rsi().iloc[-1]
    ema = EMAIndicator(close=df['close'], window=200).ema_indicator().iloc[-1]
    last_price = df['close'].iloc[-1]

    if rsi > 60 and last_price > ema:
        return "BUY"
    elif rsi < 40 and last_price < ema:
        return "SELL"
    else:
        return "HOLD"

def get_token_info_from_coingecko(symbol):
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        coins = requests.get(url).json()
        matched = [coin for coin in coins if coin['symbol'].lower() == symbol.lower()[:len(coin['symbol'])]]
        if matched:
            coin_id = matched[0]['id']
            info_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            info = requests.get(info_url).json()
            market_cap = info.get('market_data', {}).get('market_cap', {}).get('usd', 0)
            genesis_date = info.get('genesis_date', 'Unknown')
            return market_cap, genesis_date
        return 0, 'Unknown'
    except:
        return 0, 'Unknown'

def get_dexscreener_top():
    url = "https://api.dexscreener.com/latest/dex/pairs"
    res = requests.get(url).json()
    pairs = res.get("pairs", [])
    data = []
    for p in pairs:
        symbol = p.get('baseToken', {}).get('symbol', '-') + "/" + p.get('quoteToken', {}).get('symbol', '-')
        volume = float(p.get('volume', {}).get('h1', 0))
        change = float(p.get('priceChange', {}).get('h1', 0))
        data.append({
            'symbol': symbol,
            'priceChange%': change,
            'volume_1h': volume,
            'chain': p.get('chainId', '-')
        })
    df = pd.DataFrame(data)
    return df.sort_values(by='priceChange%', ascending=False).head(20)

# === Streamlit UI ===
st.set_page_config(page_title="Crypto Pump Signal Dashboard", layout="wide")
st.title("Real-Time Crypto Pump Signal Tracker")

refresh_interval = st.slider("Auto-refresh interval (seconds):", 10, 60, 30)
placeholder = st.empty()

while True:
    with placeholder.container():
        st.subheader("Binance Top Gainers with Technical Signals")
        binance_df = get_binance_top_gainers()
        signals, caps, dates = [], [], []

        for symbol in binance_df['symbol']:
            signal = analyze_technical_signals(symbol)
            coingecko_symbol = symbol.replace('USDT','').lower()
            cap, date = get_token_info_from_coingecko(coingecko_symbol)
            signals.append(signal)
            caps.append(cap)
            dates.append(date)

        binance_df['Signal'] = signals
        binance_df['Market Cap (USD)'] = caps
        binance_df['Token Age'] = dates
        binance_df['Pump Signal'] = binance_df.apply(lambda row: "Yes" if row['priceChangePercent'] > 15 or row['Signal'] == "BUY" else "No", axis=1)
        binance_df['Dump Signal'] = binance_df.apply(lambda row: "Yes" if row['Signal'] == "SELL" else "No", axis=1)
        st.dataframe(binance_df, use_container_width=True)

        st.subheader("Top DEX Gainers")
        dex_df = get_dexscreener_top()
        dex_df['DEX Pump Signal'] = dex_df['priceChange%'].apply(lambda x: "Yes" if x > 30 else "No")
        st.dataframe(dex_df, use_container_width=True)

        st.caption("Signals based on RSI/EMA for Binance. DEX tokens flagged with price change > 30% in 1h")

    time.sleep(refresh_interval)
    placeholder.empty()
