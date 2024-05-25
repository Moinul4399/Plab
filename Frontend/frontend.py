import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from collections import Counter

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
    st.set_page_config(page_title="Pizzeria Dashboard", page_icon="🍕", layout="wide")

    st.sidebar.markdown("<h1 style='text-align: center; color: white;'>Pizzeria Dashboard</h1>", unsafe_allow_html=True)

    # Fetch top stores data
    top_stores_data = fetch_data("http://localhost:5000/api/top_stores")
    if top_stores_data and 'top_stores' in top_stores_data:
        top_stores_df = pd.DataFrame(top_stores_data['top_stores'])
        st.subheader("Top Stores Based on Revenue")
        st.dataframe(top_stores_df.style.highlight_max(subset=['total_revenue'], color='lightgreen'))
        fig = px.bar(top_stores_df, x='storeID', y='total_revenue', color='city', title="Top Stores Revenue")
        st.plotly_chart(fig)
    else:
        st.error("No data available or unable to fetch data.")

    # Fetch unique pizza ingredients data
    unique_ingredients_data = fetch_data("http://localhost:5000/api/unique_pizza_ingredients")
    if unique_ingredients_data and 'unique_pizza_ingredients' in unique_ingredients_data:
        ingredients_list = [ingredient['ingredients'] for ingredient in unique_ingredients_data['unique_pizza_ingredients']]
        ingredients_flat = ', '.join(ingredients_list).split(', ')
        ingredients_count = Counter(ingredients_flat)
        
        st.subheader("Ingredients Frequency Across All Pizzas")
        ingredients_df = pd.DataFrame(ingredients_count.items(), columns=['Ingredient', 'Frequency'])
        fig_ingredients = px.bar(ingredients_df, x='Ingredient', y='Frequency', title="Frequency of Ingredients")
        st.plotly_chart(fig_ingredients)
    else:
        st.error("No ingredients data available or unable to fetch data.")

if __name__ == "__main__":
    main()
