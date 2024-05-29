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


# Funktion für das Haupt-Dashboard
def main():
    # Streamlit-Seitenkonfiguration
    st.set_page_config(
        page_title="Pizzaria Dashboard",
        page_icon="🍕",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Seitenleiste
    st.sidebar.image("images/CaptainPizza.png", width=170, use_column_width=False)
    st.sidebar.markdown("<h1 style='text-align: center; color: white; margin-left: -30px;'>🍕 Pizzaria Dashboard</h1>", unsafe_allow_html=True)

    # Filtermöglichkeiten
    view_option = st.sidebar.radio("Select your view:", ("Overview", "Regionview", "Storeview"))

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

if __name__ == "_main_":
    main()