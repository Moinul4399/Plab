import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import statsmodels.api as sm
import altair as alt
import datetime as dt




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
                boxpoints='all',  # Alle Datenpunkte anzeigen
                jitter=0.5,      # Jitter für Datenpunkte
                whiskerwidth=0.2,  # Breite der Whisker
                marker_size=2,    # Größe der Marker
                line_width=1      # Breite der Linien
            ))

        # Layout anpassen
        fig.update_layout(
            xaxis_title="Pizza Type",
            yaxis_title="Repeat Orders",
            showlegend=False
        )

        return fig
    else:
        st.error("Fehler beim Abrufen der Boxplot-Daten")
        return go.Figure()

    
## Scatter mit Linie
# Funktion zum Erstellen der Scatter Plots
def create_scatter_plots():
    scatter_data = fetch_data("http://localhost:5000/api/scatterplot")
    if scatter_data:

        # Umwandeln der empfangenen Daten in einen DataFrame
        df = pd.DataFrame(scatter_data)

        # Umbenennen der Spalten
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        # Konvertiere Orders und Revenue in numerische Werte
        df['Orders'] = pd.to_numeric(df['Orders'], errors='coerce')
        df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')



        # Scatter Plots für jedes Jahr erstellen
        years = [2020, 2021, 2022]
        fig = make_subplots(rows=1, cols=3, subplot_titles=[str(year) for year in years])

        for i, year in enumerate(years, start=1):
            df_year = df[df['Year'] == str(year)]
            if not df_year.empty:
                scatter = go.Scatter(
                    x=df_year['Orders'],
                    y=df_year['Revenue'],
                    mode='markers',
                    name=f'{year}',
                    marker=dict(size=10),
                    hovertemplate='<br><b>Store ID:</b> %{customdata[0]}<br>'
                                  '<b>Total Orders:</b> %{x:.0f}<br>'
                                  '<b>Revenue:</b> %{y:.1f}k<extra></extra>',
                    customdata=df_year[['Store ID']]
                )
                fig.add_trace(scatter, row=1, col=i)
                
                
                # Hinzufügen der Trendlinie
                trendline = px.scatter(
                    df_year,
                    x='Orders',
                    y='Revenue',
                    trendline='ols'
                ).data[1]
                fig.add_trace(trendline, row=1, col=i)

        fig.update_layout(
            title_text="Scatter Plots of Orders vs Revenue with Trendline",
            showlegend=False,
            margin={"r":0,"t":30,"l":0,"b":0}
        )

        for i in range(1, 4):
            fig.update_xaxes(title_text='Total Orders', row=1, col=i)
            fig.update_yaxes(title_text='Revenue', row=1, col=i)

        return fig
    else:
        st.error("Keine Daten empfangen")
        return None
    
    
    
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
    
    
# Funktion zum Erstellen des Liniendiagramms der wöchentlichen Umsätze
def show_weekly_revenue(store_id):
    endpoint = "http://localhost:5000/api/revenue_per_weekday"
    data = fetch_data(endpoint)
    
    if data:
        revenue_data = data.get('revenue_per_weekday', [])
        if not revenue_data:
            st.error("Keine Umsatzdaten verfügbar")
            return

        df = pd.DataFrame(revenue_data)
        st.write("Fetched data:", df)  # Debugging-Ausgabe

        df = df[df['storeid'] == store_id]
        st.write(f"Filtered data for store {store_id}:", df)  # Debugging-Ausgabe

        if df.empty:
            st.error(f"Keine Umsatzdaten für Store {store_id} verfügbar")
            return

        # Mapping von Wochentagen
        days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        df['Day'] = df['order_day_of_week'].map(days_map)

        # Sortiere die Wochentage in der richtigen Reihenfolge
        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['Day'] = pd.Categorical(df['Day'], categories=ordered_days, ordered=True)

        st.write("Processed data for plotting:", df)  # Debugging-Ausgabe

        # Altair zur Visualisierung verwenden
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('Day', sort=ordered_days, title='Day of the Week'),
            y=alt.Y('total_revenue', title='Total Revenue')
        ).properties(
            title=f'Weekly Revenue for Store {store_id}',
            width=700,
            height=400
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.error("Fehler beim Abrufen der wöchentlichen Umsätze")


# Neue Scatter Plot Linie für Pizza als Alternative
# Dummy-Daten erstellen
data = {
    'name': ['Margherita Pizza', 'Pepperoni Pizza', 'Hawaiian Pizza', 'Veggie Pizza'] * 4,
    'size': ['Small', 'Medium', 'Large', 'Extra Large'] * 4,
    'launch': [dt.datetime(2018, 1, 1), dt.datetime(2019, 5, 10), dt.datetime(2020, 8, 15), dt.datetime(2021, 2, 20)] * 4,
    'orders': np.random.randint(100, 1000, 16),
    'revenue': np.random.randint(1000, 10000, 16)
}

# DataFrame erstellen
df = pd.DataFrame(data)

# Konvertiere das Release-Datum in ein Datetime-Format
df['launch'] = pd.to_datetime(df['launch'])

# Filter für das erste Jahr nach dem Release-Datum
df['end_date'] = df['launch'] + pd.DateOffset(years=1)

# Aggregiere Daten für jede Pizza im ersten Jahr nach dem Release-Datum
df_aggregated = df.groupby(['name', 'size', 'launch', 'end_date']).agg({
    'orders': 'sum',
    'revenue': 'sum'
}).reset_index()

# Scatter-Plot und Regressionslinie erstellen
def plot_pizza_performance():
    fig = make_subplots(rows=1, cols=1, subplot_titles=["Pizza Performance in First Year After Release"])

    scatter = go.Scatter(
        x=df_aggregated['orders'],
        y=df_aggregated['revenue'],
        mode='markers',
        text=df_aggregated.apply(lambda row: f"Pizza Name: {row['name']}<br>Size: {row['size']}<br>Release Date: {row['launch'].date()}<br>Orders: {row['orders']}<br>Revenue: ${row['revenue']}", axis=1),
        hoverinfo='text'
    )
    fig.add_trace(scatter, row=1, col=1)

    # OLS-Regression berechnen
    X = sm.add_constant(df_aggregated['orders'])
    y = df_aggregated['revenue']
    model = sm.OLS(y, X).fit()

    # Trendlinie hinzufügen
    df_aggregated['predicted_revenue'] = model.predict(X)
    trendline = go.Scatter(
        x=df_aggregated['orders'],
        y=df_aggregated['predicted_revenue'],
        mode='lines',
        name='Trendline'
    )
    fig.add_trace(trendline, row=1, col=1)

    fig.update_layout(
        xaxis_title='Total Orders',
        yaxis_title='Revenue'
    )

    return fig






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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Location Map", "Store Revenue Map", "Weekly Revenue", "Pizza Boxplot", "Scatter Plots", "Pizza Sales Scatter Plot", "Pizza Performance Plot"])

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
        st.header("Weekly Revenue")
        data = fetch_data("http://localhost:5000/api/revenue_per_weekday")
        if data:
            revenue_data = data.get('revenue_per_weekday', [])
            if not revenue_data:
                st.error("Keine Umsatzdaten verfügbar")
            else:
                df = pd.DataFrame(revenue_data)
                st.write("Fetched data for all stores:", df)  # Debugging-Ausgabe

                store_options = df['storeid'].unique()
                selected_store = st.selectbox("Wähle eine Store-ID", store_options)
                show_weekly_revenue(selected_store)
        else:
            st.error("Fehler beim Abrufen der Daten")
            
            
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
        st.header("Pizza Performance Scatter Plot")
        fig_pizza_performance = plot_pizza_performance()
        if fig_pizza_performance:
            st.plotly_chart(fig_pizza_performance, use_container_width=True)
        else:
            st.error("Error fetching pizza performance data")
        
        


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
    st.title("Storeview Dashboard")

     # Monthly Revenue anzeigen        
    st.title("monthly Revenue for store")
    store_id = st.text_input("Gib eine Store-ID ein, um die monatlichen Umsätze anzuzeigen")
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