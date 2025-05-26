
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Crypto Pump Detector", layout="wide")

st.title("🚀 Live Crypto Pump Detector (Binance Top Gainers)")

@st.cache_data(ttl=60)
def get_binance_top_gainers():
    url = "https://api.binance.com/api/v3/ticker/24hr"

    try:
        res = requests.get(url, timeout=10).json()

        # Validate the API response
        if not isinstance(res, list):
            st.error("❌ Binance API did not return expected list of data.")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(res)

        # Required fields check
        required_columns = ['symbol', 'priceChangePercent', 'quoteVolume']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"❌ Missing expected column: {col}")
                return pd.DataFrame()

        # Convert necessary fields to float
        df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
        df['volume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')

        # Sort and select top gainers
        top = df.sort_values(by='priceChangePercent', ascending=False)

        return top[['symbol', 'priceChangePercent', 'volume']].head(20)

    except Exception as e:
        st.error(f"❌ Failed to fetch or process Binance data: {e}")
        return pd.DataFrame()

# Get top gainers
binance_df = get_binance_top_gainers()

# Show results
st.subheader("📈 Binance Top 20 Gainers (24hr)")
if not binance_df.empty and 'symbol' in binance_df.columns:
    st.dataframe(binance_df)
    st.success("✅ Live data loaded successfully.")
else:
    st.warning("⚠️ No data available or API returned unexpected result.")
