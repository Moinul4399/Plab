import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def fetch_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: Status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Pizzeria Dashboard",
        page_icon="🍕",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Hier ersetzen wir die image-Anweisung durch eine markdown-Anweisung
    st.sidebar.markdown("<h1 style='text-align: center; color: white;'>🍕 Pizzeria Dashboard</h1>", unsafe_allow_html=True)

    # Fetch top stores data
    top_stores_data = fetch_data("http://localhost:5000/api/top_stores")

    if top_stores_data and 'top_stores' in top_stores_data:
        top_stores_df = pd.DataFrame(top_stores_data['top_stores'])
        st.write("Top Stores Based on Revenue", top_stores_df)
        
        # Optionally visualize top stores data
        fig = px.bar(top_stores_df, x='storeID', y='total_revenue', color='city', title="Top Stores Revenue")
        st.plotly_chart(fig)

    else:
        st.write("No data available or unable to fetch data.")

if __name__ == "__main__":
    main()
