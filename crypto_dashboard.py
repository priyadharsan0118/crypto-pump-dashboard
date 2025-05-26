
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Crypto Pump Detector", layout="wide")
st.title("ðŸš€ Live Crypto Pump Detector (Top Gainers with Signals)")

@st.cache_data(ttl=180)
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
    except Exception as e:
        st.error(f"Error fetching top gainers: {e}")
        return pd.DataFrame()

def get_price_history(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '1',
            'interval': 'hourly'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if 'prices' not in data:
            return pd.DataFrame()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        return pd.DataFrame()

def generate_signal(df):
    if len(df) < 4:
        return "âš ï¸ No Signal"
    recent = df['price'].iloc[-1]
    avg_recent = df['price'].iloc[-3:].mean()
    avg_early = df['price'].iloc[:3].mean()
    change_pct = ((avg_recent - avg_early) / avg_early) * 100
    if change_pct > 3:
        return "ðŸŸ¢ Buy Signal (Pump)"
    elif change_pct < -3:
        return "ðŸ”´ Sell Signal (Dump)"
    else:
        return "âšª Hold"

top_df = get_top_gainers()
st.subheader("ðŸ“ˆ Top 10 Gainers (24h)")

if not top_df.empty:
    st.dataframe(top_df)

    for _, row in top_df.iterrows():
        with st.expander(f"{row['Name']} ({row['Symbol'].upper()}) - ${row['Current Price']:.2f}"):
            st.write("Fetching price history...")
            df = get_price_history(row['ID'])
            time.sleep(1.5)  # avoid hitting rate limits

            if not df.empty:
                signal = generate_signal(df)
                st.markdown(f"### Signal: **{signal}**")
                fig, ax = plt.subplots()
                ax.plot(df['time'], df['price'], label='Price')
                ax.set_title(f"{row['Name']} - Last 24h")
                ax.set_xlabel("Time")
                ax.set_ylabel("USD")
                ax.legend()
                st.pyplot(fig)
            else:
                st.warning("âš ï¸ Could not load price history for this token.")
else:
    st.warning("âš ï¸ No gainers data loaded.")
