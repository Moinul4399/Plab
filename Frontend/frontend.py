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
        for type, details in zip(["Store", "Customer"], [{"color": "blue", "size": 15}, {"color": "green", "size": 6}]):
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
    
    
    # Funktion zum Erstellen der Scatter Plots
def create_scatter_plots():
    scatter_data = fetch_data("http://localhost:5000/api/scatterplot")
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        # Konvertiere Orders und Revenue in numerische Werte
        df['Orders'] = pd.to_numeric(df['Orders']).apply(lambda x: round(x))  # Auf ganze Zahlen runden
        df['Revenue'] = pd.to_numeric(df['Revenue']).round(1)  # Auf eine Dezimalstelle runden

        # Scatter Plot mit Faceting erstellen
        fig = px.scatter(
            df,
            x='Orders',
            y='Revenue',
            color='Store ID',
            facet_col='Year',
            labels={'Orders': 'Total Orders', 'Revenue': 'Revenue'}
        )

        fig.update_traces(
            hovertemplate='<br><b>Store ID:</b> %{customdata[0]}<br>'
                          '<b>Total Orders:</b> %{x:.0f}<br>'
                          '<b>Revenue:</b> %{y:.1f}k<extra></extra>',
            customdata=df[['Store ID']]
        )

        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # Entfernt "Year =" aus den Facettentiteln

        fig.update_layout(
            margin={"r":0,"t":30,"l":0,"b":0},
            xaxis_tickformat=',d',  # Entfernt Dezimalstellen von der x-Achse
            yaxis_tickformat=',.1f'  # Eine Dezimalstelle auf der y-Achse
        )

        return fig
    else:
        return None


    
#monthly bar chart
# Funktion zum Erstellen des Säulendiagramms der monatlichen Revenues
def show_monthly_sales(store_id, year):
    endpoint = f"http://localhost:5000/api/store_monthly_revenues"
    data = fetch_data(endpoint)
    
    if data:
        store_data = next((item for item in data['store_monthly_revenues'] if item['storeid'] == store_id), None)
        
        if store_data:
            monthly_sales_data = {
                month: revenue
                for month, revenue in store_data['monthly_revenues'].items()
                if month.startswith(year)
            }
            
            if monthly_sales_data:
                monthly_sales_df = pd.DataFrame(list(monthly_sales_data.items()), columns=['Month', 'Sales'])
                monthly_sales_df['Month'] = pd.to_datetime(monthly_sales_df['Month'] + '-01')  # Monatliches Datum erstellen
                monthly_sales_df = monthly_sales_df.set_index('Month').resample('M').sum().reset_index()
                monthly_sales_df['Month'] = monthly_sales_df['Month'].dt.strftime('%B')

                fig = px.bar(monthly_sales_df, x='Month', y='Sales', title=f'Monthly Sales for Store {store_id} in {year}', labels={'Month': 'Month', 'Sales': 'Sales'})
                st.plotly_chart(fig)
            else:
                st.error(f"Keine Daten für Store {store_id} im Jahr {year} verfügbar")
        else:
            st.error(f"Keine Daten für Store {store_id} verfügbar oder kein Jahr angegeben")
    else:
        st.error("Fehler beim Abrufen der monatlichen Umsätze")
    


## Histogramm mit Dummy-Data

# Beispielhafte Daten
data = [
    {'storeid': 'Store1', 'customerid': 'Cust1', 'order_count': 3, 'year': 2020},
    {'storeid': 'Store1', 'customerid': 'Cust2', 'order_count': 2, 'year': 2020},
    {'storeid': 'Store1', 'customerid': 'Cust3', 'order_count': 4, 'year': 2021},
    {'storeid': 'Store1', 'customerid': 'Cust4', 'order_count': 1, 'year': 2021},
    {'storeid': 'Store1', 'customerid': 'Cust9', 'order_count': 5, 'year': 2022},
    {'storeid': 'Store1', 'customerid': 'Cust10', 'order_count': 2, 'year': 2022},
    {'storeid': 'Store2', 'customerid': 'Cust5', 'order_count': 5, 'year': 2020},
    {'storeid': 'Store2', 'customerid': 'Cust6', 'order_count': 3, 'year': 2020},
    {'storeid': 'Store2', 'customerid': 'Cust7', 'order_count': 2, 'year': 2021},
    {'storeid': 'Store2', 'customerid': 'Cust8', 'order_count': 4, 'year': 2021},
    {'storeid': 'Store2', 'customerid': 'Cust11', 'order_count': 3, 'year': 2022},
    {'storeid': 'Store2', 'customerid': 'Cust12', 'order_count': 1, 'year': 2022},
]

df = pd.DataFrame(data)

# Gruppierungen fpr Balkendiagramm in Histogramm
def create_grouped_bar_chart(df, store1, store2):
    if store2 == "None":
        df_filtered = df[df['storeid'] == store1]
    else:
        df_filtered = df[(df['storeid'] == store1) | (df['storeid'] == store2)]
        
    df_grouped = df_filtered.groupby(['year', 'storeid'])['order_count'].sum().reset_index()

    fig = go.Figure()

    for store in [store1, store2]:
        if store == "None":
            continue
        df_store = df_grouped[df_grouped['storeid'] == store]
        fig.add_trace(go.Bar(
            x=df_store['year'],
            y=df_store['order_count'],
            name=store,
            hovertemplate='Year: %{x}<br>Orders: %{y}'
        ))

    fig.update_layout(
        barmode='group',
        title='Customer Reorder Comparison',
        xaxis_title='Year',
        yaxis_title='Repeat Purchases',
        xaxis=dict(type='category')
    )

    return fig

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

# Dummy-Daten für das Liniendiagramm
def generate_dummy_order_data():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    years = [2018, 2019, 2020, 2021, 2022]
    data = []

    for year in years:
        for day in days:
            avg_orders = np.random.randint(50, 150)  # Zufällige Durchschnittswerte für Bestellungen
            data.append({'Year': year, 'Day': day, 'AvgOrders': avg_orders})

    return pd.DataFrame(data)

# Funktion für das Overview-Dashboard
def overview_dashboard():
    # Daten für Metriken abrufen
    metrics = fetch_data("http://localhost:5000/api/metrics")
    if metrics:
        total_customers = metrics.get('total_customers', 0)
        total_revenue = metrics.get('total_revenue', 0.0)
        average_revenue_per_store = metrics.get('average_revenue_per_store', 0.0)
    else:
        total_customers = total_revenue = average_revenue_per_store = 0

    # Kacheln mit Metriken hinzufügen
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Kunden", total_customers)
    col2.metric("Umsatz total", f"${total_revenue / 1e6:,.2f}Mio")
    col3.metric("Durchschnittsumsatz pro Store", f"${average_revenue_per_store / 1e6:,.2f} Mio")

    # Tabs für verschiedene Diagramme und Karten
    tab1, tab2, tab3, tab4 = st.tabs(["Location Map", "Store Revenue Map", "Average Orders", "Scatter Plots"])

    with tab1:
        "Location Map"
        # Location Map anzeigen
        tab1.header("Location Map for Customers and Stores")
        fig_location_map = create_location_map()
        tab1.plotly_chart(fig_location_map,
use_container_width=True)

    with tab2:
        "Store Revenue Map"
        # Store Revenue Map anzeigen
        tab2.header("Store Revenue Map")
        selected_year = tab2.selectbox('Select Year', ['2020', '2021', '2022'], key='year_filter')
        fig_sales_heatmap = create_sales_heatmap(selected_year)
        tab2.plotly_chart(fig_sales_heatmap, use_container_width=True)

    with tab3: 
        "Average Orders"
        # Durchschnittliche Bestellungen anzeigen
        tab3.header("Average Orders from Monday to Sunday (2018-2022)")
        order_data = generate_dummy_order_data()
        fig_line = px.line(order_data, x='Day', y='AvgOrders', color='Year', symbol="Year")
        tab3.plotly_chart(fig_line, use_container_width=True)
        
        
    with tab4:
        "Scatter Plots"
        # Scatter Plots anzeigen
        tab4.header("Scatter Plots of Orders vs Revenue")
        fig_scatter = create_scatter_plots()
        if fig_scatter:
            tab4.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.error("Fehler beim Abrufen der Scatter Plot Daten")

# Hauptfunktion für das Dashboard
def main():
    st.set_page_config(page_title="Pizzeria Dashboard", page_icon="🍕", layout="wide")

    # Sidebar mit Bild und Navigation
    st.sidebar.image("images/CaptainPizza.png", use_column_width=True)  # Pfad zu Ihrem Logo
    page = st.sidebar.selectbox("Navigation", ["Overview", "Storeview"])

    if page == "Overview":
        overview_dashboard()
    elif page == "Storeview":
        storeview_dashboard()


# Funktion für das Storeview-Dashboard
def storeview_dashboard():
    st.title("Storeview Dashboard")
    
    # Funktion zum Erstellen des Säulendiagramms der monatlichen Revenues
def show_monthly_sales(store_id, year):
    endpoint = f"http://localhost:5000/api/store_monthly_revenues"
    data = fetch_data(endpoint)
    
    if data:
        store_data = next((item for item in data['store_monthly_revenues'] if item['storeid'] == store_id), None)
        
        if store_data:
            monthly_sales_data = {
                month: revenue
                for month, revenue in store_data['monthly_revenues'].items()
                if month.startswith(year)
            }
            
            if monthly_sales_data:
                monthly_sales_df = pd.DataFrame(list(monthly_sales_data.items()), columns=['Month', 'Sales'])
                monthly_sales_df['Month'] = pd.to_datetime(monthly_sales_df['Month'] + '-01')  # Monatliches Datum erstellen
                monthly_sales_df = monthly_sales_df.set_index('Month').resample('M').sum().reset_index()
                monthly_sales_df['Month'] = monthly_sales_df['Month'].dt.strftime('%B')

                fig = px.bar(monthly_sales_df, x='Month', y='Sales', title=f'Monthly Sales for Store {store_id} in {year}', labels={'Month': 'Month', 'Sales': 'Sales'})
                st.plotly_chart(fig)
            else:
                st.error(f"Keine Daten für Store {store_id} im Jahr {year} verfügbar")
        else:
            st.error(f"Keine Daten für Store {store_id} verfügbar oder kein Jahr angegeben")
    else:
        st.error("Fehler beim Abrufen der monatlichen Umsätze")

## Histogramm mit Dummy-Data
# Beispielhafte Daten
data = [
    {'storeid': 'Store1', 'customerid': 'Cust1', 'order_count': 3, 'year': 2020},
    {'storeid': 'Store1', 'customerid': 'Cust2', 'order_count': 2, 'year': 2020},
    {'storeid': 'Store1', 'customerid': 'Cust3', 'order_count': 4, 'year': 2021},
    {'storeid': 'Store1', 'customerid': 'Cust4', 'order_count': 1, 'year': 2021},
    {'storeid': 'Store1', 'customerid': 'Cust9', 'order_count': 5, 'year': 2022},
    {'storeid': 'Store1', 'customerid': 'Cust10', 'order_count': 2, 'year': 2022},
    {'storeid': 'Store2', 'customerid': 'Cust5', 'order_count': 5, 'year': 2020},
    {'storeid': 'Store2', 'customerid': 'Cust6', 'order_count': 3, 'year': 2020},
    {'storeid': 'Store2', 'customerid': 'Cust7', 'order_count': 2, 'year': 2021},
    {'storeid': 'Store2', 'customerid': 'Cust8', 'order_count': 4, 'year': 2021},
    {'storeid': 'Store2', 'customerid': 'Cust11', 'order_count': 3, 'year': 2022},
    {'storeid': 'Store2', 'customerid': 'Cust12', 'order_count': 1, 'year': 2022},
]

df = pd.DataFrame(data)

# Gruppierungen fpr Balkendiagramm in Histogramm
def create_grouped_bar_chart(df, store1, store2):
    if store2 == "None":
        df_filtered = df[df['storeid'] == store1]
    else:
        df_filtered = df[(df['storeid'] == store1) | (df['storeid'] == store2)]
        
    df_grouped = df_filtered.groupby(['year', 'storeid'])['order_count'].sum().reset_index()

    fig = go.Figure()

    for store in [store1, store2]:
        if store == "None":
            continue
        df_store = df_grouped[df_grouped['storeid'] == store]
        fig.add_trace(go.Bar(
            x=df_store['year'],
            y=df_store['order_count'],
            name=store,
            hovertemplate='Year: %{x}<br>Orders: %{y}'
        ))

    fig.update_layout(
        barmode='group',
        title='Customer Reorder Comparison',
        xaxis_title='Year',
        yaxis_title='Repeat Purchases',
        xaxis=dict(type='category')
    )

    return fig


# Function to handle bar click event
def handle_bar_click(trace, points, selector):
    # Toggle the bar color on click
    new_color = 'rgba(0, 0, 0, 0)' if trace.marker.color == 'rgba(0, 0, 0, 0)' else 'red'
    trace.marker.color = [new_color if i in points.point_inds else c for i, c in enumerate(trace.marker.color)]

# Funktion für das Storeview-Dashboard
def storeview_dashboard():
    st.title("Storeview Dashboard")

     # Monthly Revenue anzeigen        
    st.title("monthly Revenue for store")
    store_id = st.text_input("Gib eine Store-ID ein, um die monatlichen Umsätze anzuzeigen")
    year = st.selectbox("Wähle ein Jahr", ['2020', '2021', '2022'])

    if store_id and year:
        show_monthly_sales(store_id, year)

        # Get the selected data for bar chart
        selected_data = df[(df['storeid'] == store_id) & (df['year'] == year)]

        # Create the grouped bar chart
        fig = create_grouped_bar_chart(df, 'Store1', 'Store2')
        fig.update_traces(selector=dict(type='bar'), selected=dict(marker=dict(color='red')))  # Initial selection

        # Add event handler for bar click
        fig.data[0].on_click(handle_bar_click)

        # Show the chart
        st.plotly_chart(fig)
        
        
    # Histogramm anzeigen in store view
    st.title('Histogramm')

    store_options = df['storeid'].unique().tolist()
    store_options.append("None")
    
    store1 = st.selectbox('Select the first store', store_options)
    store2 = st.selectbox('Select the second store (optional)', store_options, index=store_options.index("None"))

    if store1 and store1 != "None":
        fig = create_grouped_bar_chart(df, store1, store2)
        st.plotly_chart(fig)
        
        
if __name__ == "__main__":
    main()
