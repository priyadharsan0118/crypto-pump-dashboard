
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Crypto Pump Detector", layout="wide")
st.title("🚀 Live Crypto Pump Detector (with Buy/Sell Signals)")

@st.cache_data(ttl=120)
def get_top_gainers():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'percent_change_24h_desc',
        'per_page': 10,
        'page': 1,
        'price_change_percentage': '24h'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df = df[['id', 'symbol', 'name', 'price_change_percentage_24h', 'total_volume', 'current_price']]
        df.rename(columns={
            'id': 'ID',
            'symbol': 'Symbol',
            'name': 'Name',
            'price_change_percentage_24h': '24h % Change',
            'total_volume': 'Volume',
            'current_price': 'Current Price'
        }, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from CoinGecko: {e}")
        return pd.DataFrame()

def get_price_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '1',
        'interval': 'hourly'
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        prices = res['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        st.warning(f"Could not load price history for {coin_id}: {e}")
        return pd.DataFrame()

def generate_signal(df):
    if len(df) < 2:
        return "⚠️ No Signal"
    recent = df['price'].iloc[-1]
    previous = df['price'].iloc[-2]
    change_pct = ((recent - previous) / previous) * 100
    if change_pct > 2.0:
        return "🟢 Buy Signal"
    elif change_pct < -2.0:
        return "🔴 Sell Signal"
    else:
        return "⚪ Hold"

top_df = get_top_gainers()
st.subheader("📈 Top 10 Gainers (24h)")

if not top_df.empty:
    st.dataframe(top_df)

    for index, row in top_df.iterrows():
        st.markdown(f"---")
        st.subheader(f"{row['Name']} ({row['Symbol'].upper()})")
        price_df = get_price_history(row['ID'])

        if not price_df.empty:
            signal = generate_signal(price_df)
            st.write(f"Signal: **{signal}**")

            fig, ax = plt.subplots()
            ax.plot(price_df['time'], price_df['price'], label='Price')
            ax.set_title(f"{row['Name']} - Last 24h")
            ax.set_xlabel("Time")
            ax.set_ylabel("USD")
            ax.legend()
            st.pyplot(fig)
        time.sleep(1)
else:
    st.warning("⚠️ No data available.")
