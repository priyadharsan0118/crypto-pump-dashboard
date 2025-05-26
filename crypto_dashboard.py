
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Crypto Pump Detector", layout="wide")
st.title("🚀 Live Crypto Pump Detector (Top Gainers from CoinGecko)")

@st.cache_data(ttl=60)
def get_top_gainers():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'percent_change_24h_desc',
        'per_page': 20,
        'page': 1,
        'price_change_percentage': '24h'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df = df[['symbol', 'price_change_percentage_24h', 'total_volume']]
        df.rename(columns={
            'symbol': 'Symbol',
            'price_change_percentage_24h': '24h % Change',
            'total_volume': 'Volume'
        }, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from CoinGecko: {e}")
        return pd.DataFrame()

# Load data
top_gainers_df = get_top_gainers()

# Show table
st.subheader("📈 Top 20 Gainers (24h)")
if not top_gainers_df.empty:
    st.dataframe(top_gainers_df)
else:
    st.warning("⚠️ No data available.")
