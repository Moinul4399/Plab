import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import numpy as np
import plotly.graph_objects as go

# Funktion zum Abfragen von Backend-Daten
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Löst eine Exception aus, wenn der Request fehlschlägt
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data from {url}: {e}")
        return None

# Funktion zum Erstellen der Location Map
def create_location_map():
    store_data = fetch_data("http://localhost:5000/api/store_locations")
    customer_data = fetch_data("http://localhost:5000/api/customer_locations")

    if store_data and customer_data:
        store_df = pd.DataFrame(store_data['store_locations'])
        customer_df = pd.DataFrame(customer_data['customer_locations'])

        store_df['Type'] = 'Store'
        customer_df['Type'] = 'Customer'
        data = pd.concat([store_df, customer_df], ignore_index=True)

        fig = go.Figure()
        for type, details in zip(["Store", "Customer"], [{"color": "red", "size": 15}, {"color": "green", "size": 6}]):
            df = data[data["Type"] == type]
            fig.add_trace(go.Scattergeo(
                lon=df['longitude'],
                lat=df['latitude'],
                text=df['city'] + ' (' + df['Type'] + ')' if 'city' in df.columns else df['Type'], 
                marker=dict(
                    size=details["size"],
                    color=details["color"],
                    line=dict(width=1, color='rgba(0,0,0,0)')
                ),
                hovertemplate='%{text}<extra></extra>',
                name=type
            ))

        fig.update_layout(
            showlegend=True,
            legend=dict(
                x=1.05,
                y=0.5,
                font=dict(
                    size=14,
                ),
                bgcolor="rgba(0, 0, 0, 0)",
                bordercolor="Black",
                borderwidth=0
            ),
            geo=dict(
                projection_type='albers usa',  # Fokus auf die USA
                showland=True,
                landcolor="rgb(217, 217, 217)",
                subunitcolor="rgb(255, 255, 255)",
                subunitwidth=0.5,
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig
    else:
        return go.Figure()

# Funktion zum Erstellen der Umsatz-Heatmap
def create_sales_heatmap(selected_year):
    revenue_data = fetch_data(f"http://localhost:5000/api/store_annual_revenues")
    if revenue_data:
        data = pd.DataFrame(revenue_data['store_annual_revenues'])
        data_year = data[['latitude', 'longitude', 'city', f'revenue_{selected_year}']].copy()
        data_year['Revenue'] = pd.to_numeric(data_year[f'revenue_{selected_year}'])

        fig = px.scatter_geo(data_year, lat='latitude', lon='longitude', hover_name='city',
                             size='Revenue', color='city',
                             size_max=30, projection='albers usa')  # Fokus auf die USA

        fig.update_traces(hovertemplate='%{hovertext}<br>Revenue: %{marker.size:$,.0f}')
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            geo=dict(
                scope='north america',  # Beschränkt die Karte auf Nordamerika
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
            )
        )
        return fig
    else:
        return px.scatter_geo()

# Dummydaten
def generate_dummy_order_data():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    years = [2018, 2019, 2020, 2021, 2022]
    data = []

    for year in years:
        for day in days:
            avg_orders = np.random.randint(50, 150)  # Zufällige Durchschnittswerte für Bestellungen
            data.append({'Year': year, 'Day': day, 'AvgOrders': avg_orders})

    return pd.DataFrame(data)

# Hauptfunktion für das Dashboard
def main():
    st.set_page_config(page_title="Pizzeria Dashboard", page_icon="🍕", layout="wide")

    # Dummy-Daten laden
    order_data = generate_dummy_order_data()

    # Kacheln mit Metriken hinzufügen
    col1, col2, col3 = st.columns(3)
    col1.metric("Stores", "32")
    col2.metric("Pizza Categories", "36")
    col3.metric("Total Revenue 2022", "$18494714.60")

    # Location Map
    st.header("Location Map for Customers and Stores")
    fig_location_map = create_location_map()
    st.plotly_chart(fig_location_map, use_container_width=True)

    # Store Revenue Map mit Filter
    st.header("Store Revenue Map")
    selected_year = st.selectbox('Select Year', ['2018', '2019', '2020', '2021', '2022'], key='year_filter')
    fig_sales_heatmap = create_sales_heatmap(selected_year)
    st.plotly_chart(fig_sales_heatmap, use_container_width=True)

    # Liniendiagramm für durchschnittliche Bestellungen
    st.header("Average Orders from Monday to Sunday (2018-2022)")
    fig_line = px.line(order_data, x='Day', y='AvgOrders', color='Year', symbol="Year")
    st.plotly_chart(fig_line, use_container_width=True)

if __name__ == "__main__":
    main()