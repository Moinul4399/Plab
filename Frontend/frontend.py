import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import statsmodels.api as sm
import altair as alt


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
        
        # Zuerst Kunden-Daten, dann Store-Daten, damit Stores oben angezeigt werden
        data = pd.concat([customer_df, store_df], ignore_index=True)

        fig = go.Figure()
        for type, details in zip(["Customer", "Store"], [{"color": "green", "size": 6}, {"color": "blue", "size": 15}]):
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

        # Set focus on a specific point (latitude and longitude)
        focus_lat = 37.7749  # Beispielkoordinate (San Francisco)
        focus_lon = -122.4194  # Beispielkoordinate (San Francisco)

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
                center=dict(lat=focus_lat, lon=focus_lon),  # Fokus auf eine bestimmte Stelle
                showland=True,
                landcolor="rgb(217, 217, 217)",
                subunitcolor="rgb(255, 255, 255)",
                subunitwidth=0.5,
                fitbounds="locations",  # optional: Zoom anpassen, um alle Punkte einzuschließen
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig
    else:
        return go.Figure()

    

# Funktion zum Erstellen des Boxplot-Diagramms
def create_pizza_boxplot():
    # Backend-Daten abrufen
    url = "http://localhost:5000/api/boxplot_metrics"
    boxplot_data = fetch_data(url)

    if boxplot_data:
        # Erstelle das Boxplot-Diagramm
        fig = go.Figure()

        for pizza, stats in boxplot_data.items():
            fig.add_trace(go.Box(
                y=[stats["min"], stats["lower_whisker"], stats["q1"], stats["median"], stats["q3"], stats["upper_whisker"], stats["max"]],
                name=pizza,
                boxpoints=False,  # Keine Datenpunkte anzeigen
                whiskerwidth=0.2,  # Breite der Whisker
                marker_size=2,    # Größe der Marker
                line_width=1      # Breite der Linien
            ))

        # Layout anpassen
        fig.update_layout(
            xaxis_title="Pizza Type",
            yaxis_title="Repeat Orders",
            showlegend=False,
            yaxis=dict(range=[0, 350])  # Y-Achsenbereich erweitern
        )

        return fig
    else:
        st.error("Fehler beim Abrufen der Boxplot-Daten")
        return go.Figure()

    
## Scatter mit Linie
# Funktion zum Erstellen der Scatter Plots mit Regressionslinien und Faceting
def create_scatter_plots():
    scatter_data = fetch_data("http://localhost:5000/api/scatterplot")
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        # Konvertiere Orders und Revenue in numerische Werte
        df['Orders'] = pd.to_numeric(df['Orders']).apply(lambda x: round(x))  # Auf ganze Zahlen runden
        df['Revenue'] = pd.to_numeric(df['Revenue']).round(1)  # Auf eine Dezimalstelle runden

        # Scatter Plot mit Faceting und Regressionslinien erstellen
        fig = px.scatter(
            df,
            x='Orders',
            y='Revenue',
            color='Store ID',
            facet_col='Year',
            trendline='ols',
            trendline_scope='overall',
            trendline_color_override='cyan',
            labels={'Orders': 'Total Orders', 'Revenue': 'Revenue'}
        )

        # Extrahiere und ordne die Traces neu, um die Trendlinien zuerst hinzuzufügen
        trendline_traces = [trace for trace in fig.data if 'trendline' in trace.name]
        scatter_traces = [trace for trace in fig.data if 'trendline' not in trace.name]

        # Leere die Figur und füge zuerst die Trendlinien, dann die Scatter-Punkte hinzu
        fig.data = ()
        for trace in trendline_traces + scatter_traces:
            fig.add_trace(trace)

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

    
    
# monthly bar chart
# Funktion zum Erstellen des Säulendiagramms der monatlichen Revenues
# monthly bar chart
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


    
# Funktion zum Erstellen des Histogramms für Kundenbestellungsvergleiche
def create_grouped_bar_chart(store1, store2):
    endpoint = f"http://localhost:5000/api/store_yearly_avg_orders"
    data = fetch_data(endpoint)
    
    if data:
        if store2 == "None":
            df_filtered = [item for item in data if item['storeid'] == store1]
        else:
            df_filtered = [item for item in data if item['storeid'] in [store1, store2]]
        
        df_grouped = pd.DataFrame(df_filtered)
        df_grouped = df_grouped.groupby(['year', 'storeid'])['avg_orders_per_customer'].sum().reset_index()
        
        # Konvertiere die Orders in ganze Zahlen
        df_grouped['avg_orders_per_customer'] = df_grouped['avg_orders_per_customer'].round().astype(int)

        fig = go.Figure()

        for store in [store1, store2]:
            if store == "None":
                continue
            df_store = df_grouped[df_grouped['storeid'] == store]
            fig.add_trace(go.Bar(
                x=df_store['year'],
                y=df_store['avg_orders_per_customer'],
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

        st.plotly_chart(fig)
    else:
        st.error("Fehler beim Abrufen der Daten für das Histogramm")




# Funktion zum Erstellen der Revenue Map
def create_sales_heatmap(selected_year):
    revenue_data = fetch_data(f"http://localhost:5000/api/store_annual_revenues")
    if revenue_data:
        data = pd.DataFrame(revenue_data['store_annual_revenues'])
        data_year = data[['latitude', 'longitude', 'city', f'revenue_{selected_year}']].copy()
        data_year['Revenue'] = pd.to_numeric(data_year[f'revenue_{selected_year}'])

        # Sortiere die Daten nach Umsatz in absteigender Reihenfolge
        data_year = data_year.sort_values(by='Revenue', ascending=False)

        fig = px.scatter_geo(data_year, lat='latitude', lon='longitude', hover_name='city',
                             size='Revenue', color='city',
                             size_max=30, projection='albers usa')  # Fokus auf die USA

        fig.update_traces(hovertemplate='%{hovertext}<br>Revenue: %{marker.size:$,.0f}')

        # Set focus on a specific point (latitude and longitude)
        focus_lat = 37.7749  # Beispielkoordinate (San Francisco)
        focus_lon = -122.4194  # Beispielkoordinate (San Francisco)

        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            geo=dict(
                scope='north america',  # Beschränkt die Karte auf Nordamerika
                center=dict(lat=focus_lat, lon=focus_lon),  # Fokus auf eine bestimmte Stelle
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
                fitbounds="locations",  # optional: Zoom anpassen, um alle Punkte einzuschließen
            )
        )
        return fig
    else:
        return px.scatter_geo()
    
    
# Funktion zum Erstellen des Balkendiagramms der Einnahmen pro Wochentag für verschiedene Stores

def create_weekday_revenue_bar_chart(store_id):
    endpoint = "http://localhost:5000/api/revenue_per_weekday"
    data = fetch_data(endpoint)
    
    if data:
        revenue_data = data.get('revenue_per_weekday', [])
        if not revenue_data:
            st.error("Keine Umsatzdaten verfügbar")
            return

        df = pd.DataFrame(revenue_data)

        # Umwandlung der Werte in numerische Typen
        df['order_day_of_week'] = pd.to_numeric(df['order_day_of_week'])
        df['total_revenue'] = pd.to_numeric(df['total_revenue'])

        df = df[df['storeid'] == store_id]

        if df.empty:
            st.error(f"Keine Umsatzdaten für Store {store_id} verfügbar")
            return

        # Mapping von Wochentagen
        days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        df['Day'] = df['order_day_of_week'].map(days_map)

        # Sortiere die Wochentage in der richtigen Reihenfolge
        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['Day'] = pd.Categorical(df['Day'], categories=ordered_days, ordered=True)

        # Überprüfen Sie auf NaN-Werte oder andere unerwartete Daten
        if df['total_revenue'].isnull().any():
            st.error("Es gibt NaN-Werte in den Umsatzdaten")

        # Balkendiagramm erstellen
        fig = px.bar(df, x='Day', y='total_revenue', title=f'Weekly Revenue for Store {store_id}', labels={'Day': 'Day of the Week', 'total_revenue': 'Total Revenue'})
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Fehler beim Abrufen der wöchentlichen Umsätze")


# Pizza Sales Scatter Plot
# Funktion zum Erstellen des Streudiagramms für Pizza-Verkäufe und Umsatz
def create_pizza_scatter_plot():
    url = "http://localhost:5000/api/scatter_plot_pizzen"
    scatter_data = fetch_data(url)
    
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        fig = go.Figure()
        
        # Define colors and marker styles
        unique_pizza_names = df['pizza_name'].unique()
        unique_pizza_sizes = df['pizza_size'].unique()
        colors = px.colors.qualitative.Plotly
        
        # Manual color assignment
        color_map = {
            'Margherita Pizza': colors[0],
            'Pepperoni Pizza': 'peru',
            'Hawaiian Pizza': 'brown',  
            'Meat Lover\'s Pizza': colors[3],
            'Veggie Pizza': 'yellow',
            'BBQ Chicken Pizza': colors[5],
            'Buffalo Chicken Pizza': colors[6],
            'Sicilian Pizza': 'snow',
            'Oxtail Pizza': 'grey',
        }
        
        markers = ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down', 'triangle-left', 'triangle-right']
        
        for pizza_name in unique_pizza_names:
            for pizza_size in unique_pizza_sizes:
                df_filtered = df[(df['pizza_name'] == pizza_name) & (df['pizza_size'] == pizza_size)]
                if not df_filtered.empty:
                    fig.add_trace(go.Scatter(
                        x=df_filtered['total_sold'],
                        y=df_filtered['total_revenue'],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=color_map.get(pizza_name, 'black'),  # Verwende die manuelle Farbzuweisung
                            symbol=markers[list(unique_pizza_sizes).index(pizza_size) % len(markers)]
                        ),
                        name=f'{pizza_name} ({pizza_size})',
                        hovertemplate=f'<b>Pizza:</b> {pizza_name} ({pizza_size})<br><b>Sold Pizzas:</b> %{{x}}<br><b>Revenue:</b> %{{y:.2f}}M USD<extra></extra>'
                    ))
        
        fig.update_layout(
            title='Pizza Sales and Revenue by Type and Size',
            xaxis_title='Number of Pizzas Sold',
            yaxis_title='Total Revenue (USD)',
            legend_title='Pizza (Size)',
            showlegend=True
        )
        
        return fig
    else:
        return None
    
    
    
# Pie Chart für Verkauf last 6 months
# Dummy-Daten
pizza_data = {
    'PizzaType': ['Margherita', 'Pepperoni', 'Hawaiian', 'Veggie', 'BBQ Chicken', 'Supreme', 'Meat Lovers', 'Cheese', 'Sausage'],
    'TotalSales': [120, 150, 80, 90, 70, 110, 60, 100, 50]
}

sizes_data = {
    'PizzaType': ['Margherita', 'Margherita', 'Margherita', 'Margherita', 
                 'Pepperoni', 'Pepperoni', 'Pepperoni', 'Pepperoni',
                 'Hawaiian', 'Hawaiian', 'Hawaiian', 'Hawaiian',
                 'Veggie', 'Veggie', 'Veggie', 'Veggie',
                 'BBQ Chicken', 'BBQ Chicken', 'BBQ Chicken', 'BBQ Chicken',
                 'Supreme', 'Supreme', 'Supreme', 'Supreme',
                 'Meat Lovers', 'Meat Lovers', 'Meat Lovers', 'Meat Lovers',
                 'Cheese', 'Cheese', 'Cheese', 'Cheese',
                 'Sausage', 'Sausage', 'Sausage', 'Sausage'],
    'Size': ['Small', 'Medium', 'Large', 'X-Large'] * 9,
    'Sales': np.random.randint(20, 50, size=36)
}

df_pizza = pd.DataFrame(pizza_data)
df_sizes = pd.DataFrame(sizes_data)

# Funktion zum Erstellen des Donut-Diagramms
def create_pizza_donut():
    fig = px.pie(df_pizza, values='TotalSales', names='PizzaType', hole=0.3, title='Distribution of Pizza Types')
    fig.update_traces(textinfo='label', hovertemplate='<b>%{label}</b><br>Sales: %{value}<br>Percentage: %{percent:.2%}')
    return fig


    
    
    


# Funktion zum Erstellen des Tortendiagramms für Bestellungen pro Stunde
def create_orders_pie_chart(store_id):
    url = "http://localhost:5000/api/store_orders_per_hour"
    data = fetch_data(url)
    
    if data:
        df = pd.DataFrame(data['store_orders_per_hour'])
        df = df[df['storeid'] == store_id]
        
        if df.empty:
            st.error(f"No order data available for store {store_id}")
            return go.Figure()
        
        # Gruppierung der Daten in 4-Stunden-Intervalle
        df['order_hour'] = df['order_hour'].astype(int)
        bins = [0, 4, 8, 12, 16, 20, 24]
        labels = ['00-04', '04-08', '08-12', '12-16', '16-20', '20-24']
        df['hour_group'] = pd.cut(df['order_hour'], bins=bins, labels=labels, right=False)
        
        grouped_df = df.groupby('hour_group')['total_orders_per_hour'].sum().reset_index()

        # Tortendiagramm erstellen
        fig = px.pie(grouped_df, values='total_orders_per_hour', names='hour_group', title=f'Total Orders per Hour for Store {store_id} in 4-Hour Intervals')
        
        return fig
    else:
        return go.Figure()

        
        
# Tabelle Pizza category nach Orders 
def pizza_orders_tab():
    st.header("Pizza Orders Table")
    
    # URL der Backend-API
    API_URL = "http://localhost:5000/api/pizza_orders"  # Passen Sie die URL an Ihre Konfiguration an

    # Daten von der API abrufen
    data = fetch_data(API_URL)

    if data and "pizza_orders_by_category" in data:
        pizza_orders = data["pizza_orders_by_category"]
        df = pd.DataFrame(pizza_orders)
        
        # Pivot-Tabelle erstellen
        df_pivot = df.pivot_table(
            index='pizza_category',
            columns='order_year',
            values='total_orders',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Stellen Sie sicher, dass die Werte numerisch sind
        df_pivot = df_pivot.apply(pd.to_numeric, errors='ignore')

        # Gesamtbestellungen hinzufügen
        df_pivot['Total Orders'] = df_pivot.iloc[:, 1:].sum(axis=1)
        
        # Spaltennamen anpassen
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={'pizza_category': 'Pizza Category', 2020: '2020 Orders', 2021: '2021 Orders', 2022: '2022 Orders'})

        # Index-Spalte hinzufügen und bei 1 beginnen lassen
        df_pivot.index = df_pivot.index + 1
        df_pivot.index.name = "Index"

        # Daten in einer Tabelle anzeigen
        if not df_pivot.empty:
            st.dataframe(df_pivot)
        else:
            st.write("No data available.")
    else:
        st.write("Failed to fetch data from the API.")

    
    
# Tabelle top 5 Stores 
def top_5_stores_tab():
    st.header("Top 5 Stores Revenue")
    
    # URL der Backend-API
    API_URL = "http://localhost:5000/api/top_5_stores"  # Passen Sie die URL an Ihre Konfiguration an

    # Daten von der API abrufen
    data = fetch_data(API_URL)

    if data and "top_5_stores" in data:
        top_stores = data["top_5_stores"]
        df = pd.DataFrame(top_stores)
        
        # Pivot-Tabelle erstellen
        df_pivot = df.pivot_table(
            index='storeid',
            columns='year',
            values='annual_sales',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Stellen Sie sicher, dass die Werte numerisch sind
        df_pivot = df_pivot.apply(pd.to_numeric, errors='ignore')

        # Gesamtumsatz hinzufügen
        df_pivot['Total Sales'] = df_pivot.iloc[:, 1:].sum(axis=1)
        
        # Spaltennamen anpassen
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={'storeid': 'Store ID', 2020: '2020 Sales', 2021: '2021 Sales', 2022: '2022 Sales'})

        # Index-Spalte hinzufügen und bei 1 beginnen lassen
        df_pivot.index = df_pivot.index + 1
        df_pivot.index.name = "Index"

        # Daten in einer Tabelle anzeigen
        if not df_pivot.empty:
            st.dataframe(df_pivot)
        else:
            st.write("No data available.")
    else:
        st.write("Failed to fetch data from the API.")

        
        
# Funktion für das Overview-Dashboard
def overview_dashboard():
    # Daten für Metriken abrufen
    metrics = fetch_data("http://localhost:5000/api/metrics")
    if metrics:
        new_customers_2022 = metrics.get('new_customers_2022', 0)
        new_customers_change = metrics.get('new_customers_change', 0.0)
        total_revenue_2022 = metrics.get('total_revenue_2022', 0.0)
        total_revenue_change = metrics.get('total_revenue_change', 0.0)
        avg_revenue_per_store_2022 = metrics.get('avg_revenue_per_store_2022', 0.0)
        avg_revenue_per_store_change = metrics.get('avg_revenue_per_store_change', 0.0)
    else:
        new_customers_2022 = total_revenue_2022 = avg_revenue_per_store_2022 = 0
        new_customers_change = total_revenue_change = avg_revenue_per_store_change = 0.0

    # Kacheln mit Metriken hinzufügen
    col1, col2, col3 = st.columns(3)
    col1.metric("New Customers 2022", new_customers_2022, f"{new_customers_change:.2f}%")
    col2.metric("Total Revenue 2022", f"${total_revenue_2022 / 1e6:,.2f} Mio", f"{total_revenue_change:.2f}%")
    col3.metric("Average Revenue for Store 2022", f"${avg_revenue_per_store_2022 / 1e6:,.2f} Mio", f"{avg_revenue_per_store_change:.2f}%")

  # Tabs für verschiedene Diagramme und Karten
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10,tab11 = st.tabs([
    "Location Map", "Store Revenue Map", "Weekly Revenue", "Pizza Boxplot", 
    "Scatter Plots", "Pizza Sales Scatter Plot", "Pizza Art & Size", "Orders Per Hour", 
    "Pizza Orders Table", "Top 5 Stores Revenue", "Worst 5 Stores Revenue"
    ])
    
    with tab1:
        st.header("Location Map for Customers and Stores")
        fig_location_map = create_location_map()
        st.plotly_chart(fig_location_map, use_container_width=True)

    with tab2:
        st.header("Store Revenue Map")
        selected_year = st.selectbox('Select Year', ['2020', '2021', '2022'], key='year_filter')
        fig_sales_heatmap = create_sales_heatmap(selected_year)
        st.plotly_chart(fig_sales_heatmap, use_container_width=True)

    with tab3:
        st.header("Weekday Revenue")
        store_options = fetch_data("http://localhost:5000/api/store_ids")['store_ids']
        selected_storeW = st.selectbox("Select Store ID", store_options, key='weekday_revenue_store')
        if selected_storeW:
            create_weekday_revenue_bar_chart(selected_storeW)
            
            
    with tab4:
        st.header("Repeat Orders by Pizza Type")
        fig_pizza_boxplot = create_pizza_boxplot()
        st.plotly_chart(fig_pizza_boxplot, use_container_width=True)
        
    with tab5:
        st.header("Scatter Plots of Orders vs Revenue")
        fig_scatter_plots = create_scatter_plots()
        if fig_scatter_plots:
            st.plotly_chart(fig_scatter_plots, use_container_width=True)
        else:
            st.error("Fehler beim Abrufen der Scatter Plot Daten")
            
    with tab6:
        st.header("Pizza Sales and Revenue Scatter Plot")
        fig_pizza_scatter_plot = create_pizza_scatter_plot()
        if fig_pizza_scatter_plot:
            st.plotly_chart(fig_pizza_scatter_plot, use_container_width=True)
        else:
            st.error("Error fetching pizza scatter plot data")
            
    with tab7:
        st.header("Pizza Art & Size")
        pizza_chart = create_pizza_donut()
        st.plotly_chart(pizza_chart, use_container_width=True)
        st.subheader("The data is based for 2022")
  

            
    with tab8:
        st.header("Orders Per Hour")
        store_options = fetch_data("http://localhost:5000/api/store_ids")['store_ids']
        selected_store = st.selectbox("Select Store ID", store_options)
        if selected_store:
            fig_orders_pie_chart = create_orders_pie_chart(selected_store)
            st.plotly_chart(fig_orders_pie_chart, use_container_width=True)
            
    with tab9:
        pizza_orders_tab()

    with tab10:
        top_5_stores_tab()
        
   # with tab11:
    #    worst_5_stores_tab()

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


# Funktion für das Storeview-Dashboard
def storeview_dashboard():
    # Monthly Revenue anzeigen        
    st.header("Monthly Revenue for Store")
    store_options = fetch_data("http://localhost:5000/api/store_ids")['store_ids']  # Fetching store IDs

    if store_options:
        store_id = st.selectbox('Select a store ID', store_options)
        year = st.selectbox("Wähle ein Jahr", ['2020', '2021', '2022'])

        if store_id and year:
            show_monthly_sales(store_id, year)


   

    st.header('Customer Reorder Comparison Histogram')

    store_options = fetch_data("http://localhost:5000/api/store_ids")['store_ids']  # Fetching store IDs
    if store_options:
        store_options.append("None")

        store1 = st.selectbox('Select the first store', store_options)
        store2 = st.selectbox('Select the second store (optional)', store_options, index=store_options.index("None"))

        if store1 and store1 != "None":
            create_grouped_bar_chart(store1, store2)
        
if __name__ == "__main__":
    main()
