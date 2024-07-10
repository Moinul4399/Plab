import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import callback_context
import itertools

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        return None




def create_location_map():
    store_data = fetch_data("http://localhost:5000/api/store_locations")
    customer_data = fetch_data("http://localhost:5000/api/customer_locations")

    if store_data and customer_data:
        store_df = pd.DataFrame(store_data['store_locations'])
        customer_df = pd.DataFrame(customer_data['customer_locations'])

        store_df['Type'] = 'Store'
        customer_df['Type'] = 'Customer'

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

        focus_lat = 37.7749
        focus_lon = -122.4194

        fig.update_layout(
            showlegend=True,
            legend=dict(
                x=1.05,
                y=0.5,
                font=dict(size=14),
                bgcolor="rgba(0, 0, 0, 0)",
                bordercolor="Black",
                borderwidth=0
            ),
            geo=dict(
                projection_type='albers usa',
                center=dict(lat=focus_lat, lon=focus_lon),
                showland=True,
                landcolor="rgb(217, 217, 217)",
                subunitcolor="rgb(255, 255, 255)",
                subunitwidth=0.5,
                fitbounds="locations",
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig
    else:
        return go.Figure()

# Funktion zum Erstellen der Sales Heatmap
def create_sales_heatmap(selected_year):
    revenue_data = fetch_data(f"http://localhost:5000/api/store_annual_revenues")
    if revenue_data:
        data = pd.DataFrame(revenue_data['store_annual_revenues'])
        data_year = data[['storeid', 'latitude', 'longitude', 'city', f'revenue_{selected_year}']].copy()
        data_year['Revenue'] = pd.to_numeric(data_year[f'revenue_{selected_year}'])

        data_year = data_year.sort_values(by='Revenue', ascending=False)

        fig = px.scatter_geo(data_year, lat='latitude', lon='longitude', hover_name='city',
                             size='Revenue', color='city',
                             size_max=30, projection='albers usa',
                             custom_data=['storeid'])  # Add storeid to custom_data

        fig.update_traces(hovertemplate='%{hovertext}<br>Revenue: %{marker.size:$,.0f}<br>Store ID: %{customdata[0]}')

        focus_lat = 37.7749
        focus_lon = -122.4194

        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            geo=dict(
                scope='north america',
                center=dict(lat=focus_lat, lon=focus_lon),
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
                fitbounds="locations",
            )
        )
        return fig
    else:
        return go.Figure()

#Weekday Revenue chart
def create_weekday_revenue_bar_chart(store_id):
    endpoint = "http://localhost:5000/api/revenue_per_weekday"
    data = fetch_data(endpoint)
    
    if data:
        revenue_data = data.get('revenue_per_weekday', [])
        if not revenue_data:
            return go.Figure()

        df = pd.DataFrame(revenue_data)

        df['order_day_of_week'] = pd.to_numeric(df['order_day_of_week'])
        df['total_revenue'] = pd.to_numeric(df['total_revenue'])

        df = df[df['storeid'] == store_id]

        if df.empty:
            return go.Figure()

        days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        df['Day'] = df['order_day_of_week'].map(days_map)

        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['Day'] = pd.Categorical(df['Day'], categories=ordered_days, ordered=True)

        fig = px.bar(df, x='Day', y='total_revenue', title=f'Weekly Revenue for Store {store_id}', labels={'Day': 'Day of the Week', 'total_revenue': 'Total Revenue'})

        fig.update_traces(
            hovertemplate='<b>Day:</b> %{x}<br><b>Revenue:</b> %{y:$,.0f}<extra></extra>'
        )
        
        return fig
    else:
        return go.Figure()


def create_hourly_orders_bar_chart(store_id):
    url = "http://localhost:5000/api/store_orders_per_hour"
    data = fetch_data(url)
    
    if data:
        df = pd.DataFrame(data['store_orders_per_hour'])
        df = df[df['storeid'] == store_id]
        
        if df.empty:
            print(f"No data for store {store_id}")
            return go.Figure()
        
        print("Raw data for the store:")
        print(df)

        df['order_hour'] = df['order_hour'].astype(int)
        
        # Define bins and labels for 4-hour intervals
        bins = [0, 4, 8, 12, 16, 20, 24]
        labels = ['00-04', '04-08', '08-12', '12-16', '16-20', '20-24']
        
        # Ensure the order_hour values within the bins
        df['hour_group'] = pd.cut(df['order_hour'], bins=bins, labels=labels, right=False, include_lowest=True)

        print("Data with hour groups:")
        print(df[['order_hour', 'hour_group', 'total_orders_per_hour']])
        
        # Grouping by hour_group
        grouped_df = df.groupby('hour_group')['total_orders_per_hour'].sum().reindex(labels, fill_value=0).reset_index()

        print("Grouped data:")
        print(grouped_df)

        fig = px.bar(grouped_df, x='hour_group', y='total_orders_per_hour', 
                     title=f'Total Orders per 4-Hour Intervals for Store {store_id}', 
                     labels={'hour_group': 'Hour Group:', 'total_orders_per_hour': 'Total Orders'})
        
        # Update the layout to ensure x-axis is treated as category
        fig.update_layout(
            xaxis=dict(
                type='category',
                title='Hour Group'
            ),
            yaxis=dict(
                title='Total Orders'
            )
        )

        # Update the hovertemplate
        fig.update_traces(
            hovertemplate='<b>Hour Group:</b> %{x}<br><b>Total Orders:</b> %{y:.1f}<extra></extra>'
        )
        
        return fig
    else:
        print("No data fetched from API")
        return go.Figure()

    
    

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
                monthly_sales_df['Month'] = pd.to_datetime(monthly_sales_df['Month'] + '-01')
                monthly_sales_df = monthly_sales_df.set_index('Month').resample('M').sum().reset_index()
                monthly_sales_df['Month'] = monthly_sales_df['Month'].dt.strftime('%B')

                fig = px.bar(monthly_sales_df, x='Month', y='Sales', title=f'Monthly Sales for Store {store_id} in {year}', labels={'Month': 'Month', 'Sales': 'Sales'})
                
                # Update hovertemplate
                fig.update_traces(
                    hovertemplate='<b>Month:</b> %{x}<br><b>Sales:</b> %{y:.1f}k<extra></extra>'
                )

                return fig
            else:
                return go.Figure()
        else:
            return go.Figure()
    else:
        return go.Figure()

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
                hovertemplate='<b>Year:</b> %{x}<br><b>Orders:</b> %{y:.1f}k<extra></extra>'
            ))

        fig.update_layout(
            barmode='group',
            title='Customer Reorder Comparison',
            xaxis_title='Year',
            yaxis_title='Repeat Purchases',
            xaxis=dict(type='category')
        )

        return fig
    else:
        return go.Figure()


# Scatter plot pizza
def create_pizza_scatter_plot():
    url = "http://localhost:5000/api/scatter_plot_pizzen"
    scatter_data = fetch_data(url)
    
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        fig = go.Figure()
        
        unique_pizza_names = df['pizza_name'].unique()
        unique_pizza_sizes = df['pizza_size'].unique()
        colors = px.colors.qualitative.Plotly
        
        color_map = {
            'Margherita Pizza': colors[0],
            'Pepperoni Pizza': 'peru',
            'Hawaiian Pizza': 'brown',  
            'Meat Lover\'s Pizza': colors[3],
            'Veggie Pizza': 'yellow',
            'BBQ Chicken Pizza': colors[5],
            'Buffalo Chicken Pizza': colors[6],
            'Sicilian Pizza': 'indigo',
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
                            color=color_map.get(pizza_name, 'black'),
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
            showlegend=True,
            xaxis_tickformat='~s',  # Format for large numbers with k and M suffixes on x-axis
            yaxis_tickformat='~s'   # Format for large numbers with k and M suffixes on y-axis
        )
        
        return fig
    else:
        return go.Figure()





# Funktion zur Generierung von Farben
def generate_colors():
    colors = itertools.cycle(['#FFDDC1', '#FFABAB', '#FFC3A0', '#FF677D', '#D4A5A5', '#392F5A', '#31A2AC', '#61C0BF'])
    while True:
        yield next(colors)

# Funktion zur Hervorhebung der Zeilen
def highlight_rows(df, store_colors):
    styles = []
    for i, row in df.iterrows():
        store_id = row['Store']
        color = store_colors.get(store_id, '')
        if color:
            styles.append({'if': {'filter_query': f'{{Store}} = "{store_id}"', 'column_id': 'Store'}, 'backgroundColor': color})
            styles.append({'if': {'filter_query': f'{{Store}} = "{store_id}"', 'column_id': 'Revenue in USD'}, 'backgroundColor': color})
    return styles

# Table Top 5 Stores
def create_top_stores_table(year, store_colors, color_generator):
    top_stores_data = fetch_data(f"http://localhost:5000/api/top_5_stores")
    
    if top_stores_data:
        print(f"Data for top stores: {top_stores_data}")  # Debugging-Ausgabe
        data = [store for store in top_stores_data['top_5_stores'] if store['year'] == year]  # Filter nach Jahr
        print(f"Filtered data for year {year}: {data}")  # Debugging-Ausgabe
        if data:
            df = pd.DataFrame(data)
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')  # Sicherstellen, dass annual_sales numerisch ist
            df = df.sort_values(by='annual_sales', ascending=False).head(5)  # Absteigend sortieren und Top 5 auswählen
            df = df[['storeid', 'annual_sales']]  # Spalten in der gewünschten Reihenfolge anordnen
            df.columns = ['Store', 'Revenue in USD']  # Spalten umbenennen
            
            # Formatierung der Zahlen
            df['Revenue in USD'] = df['Revenue in USD'].apply(lambda x: f"${x:,.2f}")
            
            # Farben für sich wiederholende Stores zuweisen
            store_counts = df['Store'].value_counts()
            repeating_stores = store_counts[store_counts > 1].index
            for store_id in df['Store']:
                if store_id in repeating_stores and store_id not in store_colors:
                    store_colors[store_id] = next(color_generator)
            
            # Zeilenhervorhebung basierend auf Farben
            styles = highlight_rows(df, store_colors)
            
            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
            return table, styles
    return html.Div("No data available"), []


# Table Worst 5 Stores
def create_worst_stores_table(year, store_colors, color_generator):
    worst_stores_data = fetch_data(f"http://localhost:5000/api/worst_5_stores")
    
    if worst_stores_data:
        print(f"Data for worst stores: {worst_stores_data}")  # Debugging-Ausgabe
        data = [store for store in worst_stores_data['worst_5_stores'] if store['year'] == year]  # Filter nach Jahr
        print(f"Filtered data for year {year}: {data}")  # Debugging-Ausgabe
        if data:
            df = pd.DataFrame(data)
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')  # Sicherstellen, dass annual_sales numerisch ist
            df = df.sort_values(by='annual_sales', ascending=True).head(5)  # Aufsteigend sortieren und Top 5 auswählen
            df = df[['storeid', 'annual_sales']]  # Spalten in der gewünschten Reihenfolge anordnen
            df.columns = ['Store', 'Revenue in USD']  # Spalten umbenennen
            
            # Formatierung der Zahlen
            df['Revenue in USD'] = df['Revenue in USD'].apply(lambda x: f"${x:,.2f}")
            
            # Farben für sich wiederholende Stores zuweisen
            store_counts = df['Store'].value_counts()
            repeating_stores = store_counts[store_counts > 1].index
            for store_id in df['Store']:
                if store_id in repeating_stores and store_id not in store_colors:
                    store_colors[store_id] = next(color_generator)
            
            # Zeilenhervorhebung basierend auf Farben
            styles = highlight_rows(df, store_colors)
            
            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
            return table, styles
    return html.Div("No data available"), []


# Donut Chart
def create_pizza_donut():
    url = "http://localhost:5000/api/revenues_by_pizza_type"
    donut_data = fetch_data(url)

    if donut_data:
        df_pizza = pd.DataFrame(donut_data['revenues_by_pizza_type'])

        # Gemeinsame Farbkodierung für beide Diagramme
        color_map = {
            'Margherita Pizza': '#1f77b4',
            'Pepperoni Pizza': 'peru',
            'Hawaiian Pizza': 'brown',  
            'Meat Lover\'s Pizza': '#d62728',
            'Veggie Pizza': 'yellow',
            'BBQ Chicken Pizza': '#8c564b',
            'Buffalo Chicken Pizza': '#e377c2',
            'Sicilian Pizza': 'indigo',
            'Oxtail Pizza': 'grey',
        }

        fig = px.pie(df_pizza, values='total_revenue', names='pizza_name', hole=0.3, 
                     title='Revenue by Pizza Type',
                     facet_col='order_year', facet_col_wrap=3,
                     color='pizza_name', color_discrete_map=color_map)
        
        fig.update_traces(
            textinfo='label',  # Display label text info
            textposition='inside',  # Text will only be displayed if it fits inside the slices
            insidetextorientation='radial',  # Optional: adjust text orientation
            hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Percentage: %{percent:.2%}'
        )

        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            height=550,
        )
        
        return fig
    else:
        return go.Figure()


   # Scatter Plot Revenue
def create_scatter_plots():
    scatter_data = fetch_data("http://localhost:5000/api/scatterplot")
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        df['Orders'] = pd.to_numeric(df['Orders']).apply(lambda x: round(x))
        df['Revenue'] = pd.to_numeric(df['Revenue']).round(1)

        # Adding custom data directly
        fig = px.scatter(
            df,
            x='Orders',
            y='Revenue',
            color='Store ID',
            facet_col='Year',
            trendline='ols',
            trendline_scope='overall',
            trendline_color_override='cyan',
            labels={'Orders': 'Total Orders', 'Revenue': 'Revenue'},
            hover_data={'Store ID': True},  # Ensure Store ID is included in hover data
            custom_data=['Store ID']  # Adding custom data directly here
        )

        fig.update_traces(
            hovertemplate='<br><b>Store:</b> %{customdata[0]}<br>'
                          '<b>Total Orders:</b> %{x:.0f}<br>'
                          '<b>Revenue:</b> %{y:.1f}k<extra></extra>'
        )

        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        fig.update_layout(
            margin={"r":0,"t":30,"l":0,"b":0},
            xaxis_tickformat='~s',  # Use ~s to format large numbers with k and M suffixes
            yaxis_tickformat='~s'
        )

        return fig
    else:
        return go.Figure()

def create_rfm_scatter_chart(store_id):
    url = f"http://localhost:5000/api/rfm_segments?store_id={store_id}"
    data = fetch_data(url)
    
    if data and "rfm_segments" in data:
        for store in data["rfm_segments"]:
            if store["storeid"] == store_id:
                df = pd.DataFrame(store["rfm_data"])
                
                # Create a scatter plot with segment information
                fig = px.scatter(df, 
                                 x='avg_recency', 
                                 y='avg_frequency', 
                                 size='customer_count', 
                                 color='segment',
                                 hover_data={'segment': True, 'avg_recency': True, 'avg_frequency': True, 'avg_monetary': True, 'customer_count': True},
                                 title='RFM Segments',
                                 labels={'avg_recency': 'Average Recency', 'avg_frequency': 'Average Frequency', 'avg_monetary': 'Average Monetary Value', 'customer_count': 'Number of Customers'})
                
                # Update layout for better readability
                fig.update_layout(
                    xaxis_title='Average Recency',
                    yaxis_title='Average Frequency',
                    legend_title='Segment',
                    showlegend=True,
                    margin=dict(l=40, r=0, t=40, b=30)
                )
                
                return fig
        
        print(f"No RFM data found for store_id={store_id}")
        return go.Figure()
    else:
        print(f"Error: Unexpected data format or empty data for store_id={store_id}: {data}")
        return go.Figure()


def create_aggregated_monetary_table(store_id):
    url = f"http://localhost:5000/api/rfm_segments?store_id={store_id}"
    data = fetch_data(url)
    
    if data and "rfm_segments" in data:
        for store in data["rfm_segments"]:
            if store["storeid"] == store_id:
                df = pd.DataFrame(store["rfm_data"])
                
                # Aggregate the monetary values by segment
                aggregated_data = df.groupby('segment').agg({'avg_monetary': 'sum'}).reset_index()
                aggregated_data.columns = ['Segment', 'Total Monetary Value']
                
                # Create a table to display segment and total monetary value
                table = dbc.Table(
                    # Define table header
                    [html.Thead(html.Tr([html.Th("Segment"), html.Th("Total Monetary Value")]))] +
                    # Define table body
                    [html.Tbody(
                        [html.Tr([html.Td(aggregated_data.loc[i, 'Segment']), html.Td(f"${aggregated_data.loc[i, 'Total Monetary Value']:,.2f}")]) for i in aggregated_data.index]
                    )],
                    bordered=True,
                    striped=True,
                    hover=True,
                    responsive=True
                )
                
                return table
        
        print(f"No RFM data found for store_id={store_id}")
        return "No data"
    else:
        print(f"Error: Unexpected data format or empty data for store_id={store_id}: {data}")
        return "No data"


# Beginn App Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col(html.Img(src="assets/CaptainPizza.png", style={"width": "200px"}), width=2),
        dbc.Col(html.H1("Pizzeria Dashboard", className="text-center"), width=8)
    ]),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("New Customers 2022"),
            html.H2(id="new-customers", className="card-title")
        ])), width=4),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Total Revenue 2022"),
            html.H2(id="total-revenue", className="card-title")
        ])), width=4),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Average Revenue for Store 2022"),
            html.H2(id="avg-revenue-per-store", className="card-title")
        ])), width=4)
    ]),
    dcc.Tabs([
        dcc.Tab(label='Overview', children=[
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='overview-store-dropdown',
                        options=[{'label': store_id, 'value': store_id} for store_id in fetch_data("http://localhost:5000/api/store_ids")['store_ids']],
                        value=None
                    )
                ]), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='scatterplot-revenue'), width=12)  # Hier wird der Revenue Scatterplot hinzugefügt
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pizza-donut'), width=12)  # Hier wird das Donut-Diagramm hinzugefügt
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pizza-scatterplot'), width=12)  # Hier wird der Pizza Scatterplot hinzugefügt
            ]),
            dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2020"),
                    html.Div(id='top-stores-2020')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2021"),
                    html.Div(id='top-stores-2021')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2022"),
                    html.Div(id='top-stores-2022')
                ]), width=4)
        ]),
                    dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2020"),
                    html.Div(id='worst-stores-2020')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2021"),
                    html.Div(id='worst-stores-2021')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2022"),
                    html.Div(id='worst-stores-2022')
                ]), width=4)
            ])
        ]),
        dcc.Tab(label='Storeview', children=[
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='year-dropdown',
                        options=[{'label': str(year), 'value': year} for year in range(2018, 2023)],
                        value=2022
                    ),
                    dcc.Dropdown(
                        id='store-dropdown',
                        options=[{'label': store_id, 'value': store_id} for store_id in fetch_data("http://localhost:5000/api/store_ids")['store_ids']],
                        value=None
                    )
                ]), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='revenue-map'), width=6),
                dbc.Col(dcc.Graph(figure=create_location_map()), width=6)
            ]),
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Graph(id='weekly-revenue-chart')
                ]), width=6),
                dbc.Col(html.Div([
                    dcc.Graph(id='hourly-orders-chart')
                ]), width=6)
            ]),
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Graph(id='monthly-revenue')
                ]), width=6),
                dbc.Col(dcc.Graph(id='repeat-order'), width=6)
            ])
        ]),
        dcc.Tab(label='Customerview', children=[
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Dropdown(
                        id='customer-dropdown',
                        options=[{'label': store_id, 'value': store_id} for store_id in fetch_data("http://localhost:5000/api/store_ids")['store_ids']],
                        value=None
                    )
                ]), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='customer-location-map'), width=6),
                dbc.Col(dcc.Graph(id='repeat-order-customer'), width=6)
            ])
        ])
    ])
])






@app.callback(
    [
        Output('new-customers', 'children'),
        Output('total-revenue', 'children'),
        Output('avg-revenue-per-store', 'children')
    ],
    [Input('url', 'pathname')]
)
def update_metrics(_):
    metrics = fetch_data("http://localhost:5000/api/metrics")
    if metrics:
        new_customers_2022 = metrics.get('new_customers_2022', 0)
        new_customers_change = metrics.get('new_customers_change', 0.0)
        total_revenue_2022 = metrics.get('total_revenue_2022', 0.0)
        total_revenue_change = metrics.get('total_revenue_change', 0.0)
        avg_revenue_per_store_2022 = metrics.get('avg_revenue_per_store_2022', 0.0)
        avg_revenue_per_store_change = metrics.get('avg_revenue_per_store_change', 0.0)

        return [
            f"{new_customers_2022} ({new_customers_change:.2f}%)",
            f"${total_revenue_2022 / 1e6:,.2f} Mio ({total_revenue_change:.2f}%)",
            f"${avg_revenue_per_store_2022 / 1e6:,.2f} Mio ({avg_revenue_per_store_change:.2f}%)"
        ]
    return ["No data", "No data", "No data"]

@app.callback(
    [
        Output('revenue-map', 'figure'),
        Output('weekly-revenue-chart', 'figure'),
        Output('hourly-orders-chart', 'figure'),
        Output('monthly-revenue', 'figure'),
        Output('repeat-order', 'figure')
    ],
    [
        Input('year-dropdown', 'value'),
        Input('store-dropdown', 'value')
    ]
)
def update_storeview_charts(selected_year, selected_store):
    if not selected_year or not selected_store:
        return [go.Figure()] * 5

    revenue_map_fig = create_sales_heatmap(selected_year)
    weekly_revenue_fig = create_weekday_revenue_bar_chart(selected_store)
    hourly_orders_fig = create_hourly_orders_bar_chart(selected_store)
    monthly_revenue_fig = show_monthly_sales(selected_store, str(selected_year))
    repeat_order_fig = create_grouped_bar_chart(selected_store, 'None')
    
    return revenue_map_fig, weekly_revenue_fig, hourly_orders_fig, monthly_revenue_fig, repeat_order_fig


@app.callback(
    [
        Output('scatterplot-revenue', 'figure'),
        Output('pizza-donut', 'figure'),
        Output('pizza-scatterplot', 'figure')
    ],
    [Input('overview-store-dropdown', 'value')]
)
def update_overview_charts(selected_store):
    scatterplot_revenue_fig = create_scatter_plots()
    pizza_donut_fig = create_pizza_donut()
    pizza_scatter_plot_fig = create_pizza_scatter_plot()
    
    return scatterplot_revenue_fig, pizza_donut_fig, pizza_scatter_plot_fig


@app.callback(
    [
        Output('customer-location-map', 'figure'),
        Output('repeat-order-customer', 'figure')
    ],
    [Input('customer-dropdown', 'value')]
)
def update_customer_charts(selected_store):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [go.Figure()] * 2
    
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if input_id == 'customer-dropdown':
        location_map_fig = create_location_map()  # Modify if needed to filter by store
        repeat_order_customer_fig = create_grouped_bar_chart(selected_store, 'None')  # Modify if needed to filter by store
        
        return location_map_fig, repeat_order_customer_fig
    
    return [go.Figure()] * 2

# Callback zur Aktualisierung des Dropdown-Werts basierend auf der Auswahl in der Heatmap
@app.callback(
    Output('store-dropdown', 'value'),
    [Input('revenue-map', 'clickData')]
)
def update_store_dropdown(click_data):
    if click_data and 'points' in click_data:
        selected_store = click_data['points'][0]['customdata'][0]
        return selected_store
    return None





# Table App Callback
@app.callback(
    [
        Output('top-stores-2020', 'children'),
        Output('top-stores-2021', 'children'),
        Output('top-stores-2022', 'children'),
        Output('worst-stores-2020', 'children'),
        Output('worst-stores-2021', 'children'),
        Output('worst-stores-2022', 'children')
    ],
    [Input('url', 'pathname')]
)
def update_stores_tables(_):
    store_colors = {}
    color_generator = generate_colors()
    
    top_stores_2020, top_styles_2020 = create_top_stores_table(2020, store_colors, color_generator)
    top_stores_2021, top_styles_2021 = create_top_stores_table(2021, store_colors, color_generator)
    top_stores_2022, top_styles_2022 = create_top_stores_table(2022, store_colors, color_generator)
    
    worst_stores_2020, worst_styles_2020 = create_worst_stores_table(2020, store_colors, color_generator)
    worst_stores_2021, worst_styles_2021 = create_worst_stores_table(2021, store_colors, color_generator)
    worst_stores_2022, worst_styles_2022 = create_worst_stores_table(2022, store_colors, color_generator)
    
    return top_stores_2020, top_stores_2021, top_stores_2022, worst_stores_2020, worst_stores_2021, worst_stores_2022


if __name__ == '__main__':
    app.run_server(debug=True)
