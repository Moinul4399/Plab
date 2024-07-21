from dash.dependencies import Input, Output, State
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

# Custom styles for the sidebar
sidebar_styles = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '200px',
    'padding': '20px 10px',
    'background-color': '#f8f9fa'
}

content_styles = {
    'margin-left': '210px',  # adjust according to the sidebar width
    'padding': '20px'
}

sidebar = html.Div(
    [
        html.H2('Tabs', className='display-4'),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink('Overview', href='/overview', id='overview-link'),
                dbc.NavLink('Storeview', href='/storeview', id='storeview-link'),
                dbc.NavLink('Customerview', href='/customerview', id='customerview-link'),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=sidebar_styles,
)

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        return None

# Function for creating the Sales Map
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

# Weekyday Bar chart
def create_weekday_revenue_bar_chart(store_id, selected_year):
    endpoint = "http://localhost:5000/api/revenue_per_weekday"
    data = fetch_data(endpoint)
    
    if data:
        revenue_data = data.get('revenue_per_weekday', [])
        if not revenue_data:
            print("No revenue data available")
            return go.Figure()

        df = pd.DataFrame(revenue_data)

        df['order_day_of_week'] = pd.to_numeric(df['order_day_of_week'])
        df['total_revenue'] = pd.to_numeric(df['total_revenue'])
        df['order_year'] = pd.to_numeric(df['order_year'])

        df = df[(df['storeid'] == store_id) & (df['order_year'] == int(selected_year))]

        if df.empty:
            print(f"No data for store {store_id} in year {selected_year}")
            return go.Figure()

        days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        df['Day'] = df['order_day_of_week'].map(days_map)

        ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['Day'] = pd.Categorical(df['Day'], categories=ordered_days, ordered=True)

        fig = px.bar(df, x='Day', y='total_revenue', title=f'Weekly Revenue for Store {store_id} in {selected_year}', labels={'Day': 'Day of the Week', 'total_revenue': 'Total Revenue'})

        fig.update_traces(
            hovertemplate='<b>Day:</b> %{x}<br><b>Revenue:</b> %{y:$,.0f}<extra></extra>'
        )
        
        return fig
    else:
        print("No data fetched from API")
        return go.Figure()

# Hours bar chart
def create_hourly_orders_bar_chart(store_id, selected_year):
    url = "http://localhost:5000/api/store_orders_per_hour"
    data = fetch_data(url)
    
    if data:
        df = pd.DataFrame(data['store_orders_per_hour'])
        df['order_year'] = pd.to_numeric(df['order_year'])

        df = df[(df['storeid'] == store_id) & (df['order_year'] == int(selected_year))]
        
        if df.empty:
            print(f"No data for store {store_id} in year {selected_year}")
            return go.Figure()
        
        print("Raw data for the store:")
        print(df)

        df['order_hour'] = df['order_hour'].astype(int)
        
        # Define bins and labels for 4-hour intervals
        bins = [0, 4, 8, 12, 16, 20, 24]
        labels = ['00-04', '04-08', '08-12', '12-16', '16-20', '20-24']
        
        df['hour_group'] = pd.cut(df['order_hour'], bins=bins, labels=labels, right=False, include_lowest=True)

        print("Data with hour groups:")
        print(df[['order_hour', 'hour_group', 'total_orders_per_hour']])
        
        # Grouping by hour_group
        grouped_df = df.groupby('hour_group')['total_orders_per_hour'].sum().reindex(labels, fill_value=0).reset_index()

        print("Grouped data:")
        print(grouped_df)

        fig = px.bar(grouped_df, x='hour_group', y='total_orders_per_hour', 
                     title=f'Total Orders per 4-Hour Intervals for Store {store_id} in {selected_year}', 
                     labels={'hour_group': 'Hour Group:', 'total_orders_per_hour': 'Total Orders'})
        
        fig.update_layout(
            xaxis=dict(
                type='category',
                title='Hour Group'
            ),
            yaxis=dict(
                title='Total Orders'
            )
        )

        fig.update_traces(
            hovertemplate='<b>Hour Group:</b> %{x}<br><b>Total Orders:</b> %{y:.1f}<extra></extra>'
        )
        
        return fig
    else:
        print("No data fetched from API")
        return go.Figure()

    
   
# Formate for Monthly sales
def format_sales_value(value):
    if value >= 1_000_000:
        return f'{value / 1_000_000:.1f}m'
    elif value >= 1_000:
        return f'{value / 1_000:.1f}k'
    else:
        return str(value)
 
    
# monthly sales
def show_monthly_sales(store_id, year):
    endpoint = f"http://localhost:5000/api/store_monthly_revenues"
    data = fetch_data(endpoint)
    
    if data:
        store_data = next((item for item in data['store_monthly_revenues'] if item['storeid'] == store_id), None)
        
        if store_data:
            year_str = str(year)
            monthly_sales_data = {
                month: float(revenue)
                for month, revenue in store_data['monthly_revenues'].items()
                if month.startswith(year_str)
            }
            
            if monthly_sales_data:
                monthly_sales_df = pd.DataFrame(list(monthly_sales_data.items()), columns=['Month', 'Sales'])
                monthly_sales_df['Month'] = pd.to_datetime(monthly_sales_df['Month'] + '-01')
                monthly_sales_df = monthly_sales_df.set_index('Month').resample('M').sum().reset_index()
                monthly_sales_df['Month'] = monthly_sales_df['Month'].dt.strftime('%B')
                
                monthly_sales_df['Formatted Sales'] = monthly_sales_df['Sales'].apply(format_sales_value)
                
                fig = px.bar(
                    monthly_sales_df,
                    x='Month',
                    y='Sales',
                    title=f'Monthly Sales for Store {store_id} in {year}',
                    labels={'Month': 'Month', 'Sales': 'Sales'},
                    hover_data={'Formatted Sales': True}
                )

                fig.update_traces(
                    hovertemplate='<b>Month:</b> %{x}<br><b>Sales:</b> %{customdata[0]}<extra></extra>',
                    customdata=monthly_sales_df[['Formatted Sales']].values
                )

                return fig
            else:
                return go.Figure()
        else:
            return go.Figure()
    else:
        return go.Figure()

#Repeat Customer order bar chart
def create_grouped_bar_chart(store_id):
    endpoint = f"http://localhost:5000/api/store_yearly_avg_orders?store_id={store_id}"
    data = fetch_data(endpoint)
    
    if data:
        df_grouped = pd.DataFrame(data)
        df_grouped = df_grouped.groupby(['year', 'storeid'])['repeat_customers'].sum().reset_index()
        
        df_grouped['repeat_customers'] = df_grouped['repeat_customers'].round().astype(int)

        fig = go.Figure()

        df_store = df_grouped[df_grouped['storeid'] == store_id]
        fig.add_trace(go.Bar(
            x=df_store['year'],
            y=df_store['repeat_customers'],
            name=store_id,
            hovertemplate='<b>Year:</b> %{x}<br><b>Repeat Customers:</b> %{y}<extra></extra>'
        ))

        fig.update_layout(
            barmode='group',
            title=f'Customer Reorder Comparison for Store {store_id}',
            xaxis_title='Year',
            yaxis_title='Repeat Costumers',
            xaxis=dict(type='category')
        )

        return fig
    else:
        return go.Figure()



# Format for Revenue Scatter
def format_revenue(value):
    value = float(value)  # Ensure the value is a float
    if value >= 1e6:
        return f"{value/1e6:.1f}m$"
    elif value >= 1e3:
        return f"{value/1e3:.1f}k$"
    else:
        return f"{value}$"

# Scatter Plot Pizza
def create_pizza_scatter_plot():
    url = "http://localhost:5000/api/scatter_plot_pizzen"
    scatter_data = fetch_data(url)
    
    if scatter_data:
        df = pd.DataFrame(scatter_data)

        df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce')

        df['Formatted Revenue'] = df['total_revenue'].apply(format_revenue)
        
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
                        hovertemplate=f'<b>Pizza:</b> {pizza_name} ({pizza_size})<br><b>Sold Pizzas:</b> %{{x:.0f}}<br><b>Revenue:</b> %{{customdata[0]}}<extra></extra>',
                        customdata=df_filtered[['Formatted Revenue']]  # Include formatted revenue in custom data
                    ))
        
        fig.update_layout(
            title='Pizza Sales and Revenue by Type and Size',
            xaxis_title='Number of Pizzas Sold',
            yaxis_title='Total Revenue (USD)',
            legend_title='Pizza (Size)',
            showlegend=True,
            xaxis_tickformat='~s',  
            yaxis_tickformat='~s'   
        )
        
        return fig
    else:
        return go.Figure()


def generate_colors():
    colors = itertools.cycle(['#FFDDC1', '#FFABAB', '#FFC3A0', '#FF677D', '#D4A5A5', '#392F5A', '#31A2AC', '#61C0BF'])
    while True:
        yield next(colors)

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
        data = [store for store in top_stores_data['top_5_stores'] if store['year'] == year]  # Filter nach Jahr
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
        data = [store for store in worst_stores_data['worst_5_stores'] if store['year'] == year]  # Filter nach Jahr
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


   # Format for Scatter Plot Revenue
def format_revenue(value):
    if value >= 1e6:
        return f"{value/1e6:.1f}m"
    elif value >= 1e3:
        return f"{value/1e3:.1f}k"
    else:
        return str(value)

# Scatter Plot Revenue
def create_scatter_plots():
    scatter_data = fetch_data("http://localhost:5000/api/scatterplot")
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        df['Orders'] = pd.to_numeric(df['Orders']).apply(lambda x: round(x))
        df['Revenue'] = pd.to_numeric(df['Revenue']).round(1)

        # Format revenue for hover template
        df['Formatted Revenue'] = df['Revenue'].apply(format_revenue)

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
            hover_data={'Store ID': True, 'Formatted Revenue': True},  # Ensure Store ID is included in hover data
            custom_data=['Store ID', 'Formatted Revenue']  # Adding custom data directly here
        )

        fig.update_traces(
            hovertemplate='<br><b>Store:</b> %{customdata[0]}<br>'
                          '<b>Total Orders:</b> %{x:.0f}<br>'
                          '<b>Revenue:</b> %{customdata[1]}<extra></extra>'
        )

        fig.update_layout(
            title='Revenue by orders of stores',
            margin={"r":0,"t":30,"l":0,"b":0},
            xaxis_tickformat='~s',  # Use ~s to format large numbers with k and M suffixes
            yaxis_tickformat='~s'
        )

        return fig
    else:
        return go.Figure()

#rfm-Segment
def create_rfm_scatter_chart(store_id):
    url = f"http://localhost:5000/api/rfm_segments?store_id={store_id}"
    data = fetch_data(url)
    
    if data and "rfm_segments" in data:
        for store in data["rfm_segments"]:
            if store["storeid"] == store_id:
                df = pd.DataFrame(store["rfm_data"])
                
                fig = px.scatter(df, 
                                 x='avg_recency', 
                                 y='avg_frequency', 
                                 size='customer_count', 
                                 color='segment',
                                 hover_data={'segment': True, 'avg_recency': True, 'avg_frequency': True, 'avg_monetary': True, 'customer_count': True},
                                 title='RFM Segments for 'f'{store_id}',
                                 labels={'avg_recency': 'Average Recency', 'avg_frequency': 'Average Frequency', 'avg_monetary': 'Average Monetary Value', 'customer_count': 'Number of Customers'})
                
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

#Monetary Table for rfm
def create_aggregated_monetary_table(store_id):
    url = f"http://localhost:5000/api/rfm_segments?store_id={store_id}"
    data = fetch_data(url)
    
    if data and "rfm_segments" in data:
        for store in data["rfm_segments"]:
            if store["storeid"] == store_id:
                df = pd.DataFrame(store["rfm_data"])
                
                aggregated_data = df.groupby('segment').agg({'avg_monetary': 'sum'}).reset_index()
                aggregated_data.columns = ['Segment', 'Average Monetary Value']
                
                table = dbc.Table(
                    [html.Thead(html.Tr([html.Th("Segment"), html.Th("Average Monetary Value")]))] +
                    [html.Tbody(
                        [html.Tr([html.Td(aggregated_data.loc[i, 'Segment']), html.Td(f"${aggregated_data.loc[i, 'Average Monetary Value']:,.2f}")]) for i in aggregated_data.index]
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


tab_styles = {
    'fontSize': '12px',
    'padding': '10px',
    'width': '100%',  
    'textAlign': 'center', 
    'backgroundColor': '#007bff',  
    'color': 'white',  
    'border': 'none',  
    'borderRadius': '5px',  
    'margin': '5px 0' 
}

selected_tab_styles = {
    'fontSize': '12px',
    'padding': '10px',
    'width': '100%', 
    'textAlign': 'center',  
    'backgroundColor': '#0056b3',  
    'color': 'white',  
    'border': 'none', 
    'borderRadius': '5px',  
    'margin': '5px 0'  
}

container_styles = {
    'textAlign': 'center',  
    'display': 'flex',  
    'flexDirection': 'column',  
    'justifyContent': 'flex-start',  
    'alignItems': 'center'  
}

# Define the sidebar layout
sidebar = html.Div(
    [
        html.Img(src="assets/CaptainPizza.png", style={"width": "200px"}),
        html.Hr(),
        dcc.Dropdown(
            id='global-year-dropdown',
            options=[{'label': str(year), 'value': year} for year in range(2020, 2023)],
            value=2022,
            clearable=False,
            style={"width": "100%", "marginBottom": "20px"}  # Add margin bottom to the dropdown
        ),
        html.Div(
            [
                html.Button("Overview", id="overview-link", n_clicks=0, style=tab_styles),
                html.Button("Storeview", id="storeview-link", n_clicks=0, style=tab_styles),
                html.Button("Customerview", id="customerview-link", n_clicks=0, style=tab_styles),
            ],
            style=container_styles
        )
    ],
    style={"position": "fixed", "width": "200px", "padding": "20px", "top": 0, "left": 0, "bottom": 0, "backgroundColor": "#f8f9fa"}
)

content_styles = {
    "marginLeft": "220px",
    "padding": "20px"
}


# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    dcc.Store(id='store-data'),
    dcc.Store(id='selected-store'),
    html.Div(id='page-content', style=content_styles, children=[
        html.Div(id='overview', children=[
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("New Customers 2022", className="text-center"),
                    html.H4(id="new-customers-overview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Total Revenue 2022", className="text-center"),
                    html.H4(id="total-revenue-overview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Average Revenue for Store 2022", className="text-center"),
                    html.H4(id="avg-revenue-per-store-overview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Median for Store 2022", className="text-center"),
                    html.H4(id="median_revenue_from_stores-overview", className="card-title text-center")
                ])), width=3, className="mb-4")
            ], justify="center"),
            dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2020", className="text-center"),
                    html.Div(id='top-stores-2020')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2021", className="text-center"),
                    html.Div(id='top-stores-2021')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Top 5 Stores 2022", className="text-center"),
                    html.Div(id='top-stores-2022')
                ]), width=4)
            ]),
            dbc.Row([
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2020", className="text-center"),
                    html.Div(id='worst-stores-2020')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2021", className="text-center"),
                    html.Div(id='worst-stores-2021')
                ]), width=4),
                dbc.Col(html.Div([
                    html.H3("Worst 5 Stores 2022", className="text-center"),
                    html.Div(id='worst-stores-2022')
                ]), width=4)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='scatterplot-revenue'), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pizza-donut'), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='pizza-scatterplot'), width=12)
            ]),
        ], style={'display': 'block'}),
        html.Div(id='storeview', children=[
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("New Customers 2022", className="text-center"),
                    html.H4(id="new-customers-storeview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Total Revenue 2022", className="text-center"),
                    html.H4(id="total-revenue-storeview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Average Revenue for Store 2022", className="text-center"),
                    html.H4(id="avg-revenue-per-store-storeview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Median for Store 2022", className="text-center"),
                    html.H4(id="median_revenue_from_stores-storeview", className="card-title text-center")
                ])), width=3, className="mb-4")
            ], justify="center"),
            dbc.Row([
                dbc.Col(dcc.Graph(id='revenue-map'), width=12, style={"textAlign": "center"})
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='weekly-revenue-chart'), width=6),
                dbc.Col(dcc.Graph(id='hourly-orders-chart'), width=6)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='monthly-revenue'), width=12)
            ]),
        ], style={'display': 'none'}),
        html.Div(id='customerview', children=[
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("New Customers 2022", className="text-center"),
                    html.H4(id="new-customers-customerview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Total Revenue 2022", className="text-center"),
                    html.H4(id="total-revenue-customerview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Average Revenue for Store 2022", className="text-center"),
                    html.H4(id="avg-revenue-per-store-customerview", className="card-title text-center")
                ])), width=3, className="mb-4"),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Median for Store 2022", className="text-center"),
                    html.H4(id="median_revenue_from_stores-customerview", className="card-title text-center")
                ])), width=3, className="mb-4")
            ], justify="center"),
            dbc.Row([
                dbc.Col(dcc.Graph(id='rfm-scatter-chart'), width=6),
                dbc.Col(html.Div(id='aggregated-monetary-table'), width=6)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='repeat-order'), width=12)
            ]),
        ], style={'display': 'none'})
    ])
])



@app.callback(
    [
        Output('new-customers-overview', 'children'),
        Output('total-revenue-overview', 'children'),
        Output('avg-revenue-per-store-overview', 'children'),
        Output('median_revenue_from_stores-overview', 'children'),
        Output('new-customers-storeview', 'children'),
        Output('total-revenue-storeview', 'children'),
        Output('avg-revenue-per-store-storeview', 'children'),
        Output('median_revenue_from_stores-storeview', 'children'),
        Output('new-customers-customerview', 'children'),
        Output('total-revenue-customerview', 'children'),
        Output('avg-revenue-per-store-customerview', 'children'),
        Output('median_revenue_from_stores-customerview', 'children')
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
        median_revenue_per_store = metrics.get('median_revenue_from_stores_2022', 0.0)
        median_revenue_change = metrics.get('median_revenue_change', 0.0)

        metrics_values = [
            f"{new_customers_2022} ({new_customers_change:.2f}%)",
            f"${total_revenue_2022 / 1e6:,.2f} Mio ({total_revenue_change:.2f}%)",
            f"${avg_revenue_per_store_2022 / 1e6:,.2f} Mio ({avg_revenue_per_store_change:.2f}%)",
            f"${median_revenue_per_store / 1e6:,.2f} Mio"
        ]

        return metrics_values * 3
    return ["No data"] * 12

@app.callback(
    Output('page-content', 'children'),
    [Input('overview-link', 'n_clicks'),
     Input('storeview-link', 'n_clicks'),
     Input('customerview-link', 'n_clicks')],
    [State('page-content', 'children')]
)
def display_page(n1, n2, n3, children):
    ctx = callback_context
    if not ctx.triggered:
        return children

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    for child in children:
        if child['props']['id'] == 'overview':
            child['props']['style']['display'] = 'block' if button_id == 'overview-link' else 'none'
        elif child['props']['id'] == 'storeview':
            child['props']['style']['display'] = 'block' if button_id == 'storeview-link' else 'none'
        elif child['props']['id'] == 'customerview':
            child['props']['style']['display'] = 'block' if button_id == 'customerview-link' else 'none'

    return children

@app.callback(
    [Output('store-data', 'data'), Output('selected-store', 'data')],
    [Input('global-year-dropdown', 'value'), Input('revenue-map', 'clickData')],
    [State('store-data', 'data'), State('selected-store', 'data')]
)
def update_store_data(year, clickData, store_data, selected_store):
    if store_data is None:
        store_data = {}

    store_data['revenue-map'] = create_sales_heatmap(year)
    selected_store = None
    if clickData and 'points' in clickData:
        selected_store = clickData['points'][0]['customdata'][0]

    store_data['weekly-revenue-chart'] = create_weekday_revenue_bar_chart(selected_store, year) if selected_store else go.Figure()
    store_data['hourly-orders-chart'] = create_hourly_orders_bar_chart(selected_store, year) if selected_store else go.Figure()
    store_data['monthly-revenue'] = show_monthly_sales(selected_store, year) if selected_store else go.Figure()

    store_data['rfm-scatter-chart'] = create_rfm_scatter_chart(selected_store) if selected_store else go.Figure()
    store_data['aggregated-monetary-table'] = create_aggregated_monetary_table(selected_store) if selected_store else "No data"

    return store_data, selected_store

@app.callback(
    [
        Output('revenue-map', 'figure'),
        Output('weekly-revenue-chart', 'figure'),
        Output('hourly-orders-chart', 'figure'),
        Output('monthly-revenue', 'figure')
    ],
    [
        Input('global-year-dropdown', 'value'),
        Input('revenue-map', 'clickData')
    ]
)
def update_storeview_charts(selected_year, click_data):
    if not selected_year:
        return [go.Figure()] * 4

    selected_store = click_data['points'][0]['customdata'][0] if click_data and 'points' in click_data else None


    revenue_map_fig = create_sales_heatmap(selected_year)
    if not selected_store:
        return [revenue_map_fig, go.Figure(), go.Figure(), go.Figure()]

    weekly_revenue_fig = create_weekday_revenue_bar_chart(selected_store, selected_year)
    hourly_orders_fig = create_hourly_orders_bar_chart(selected_store, selected_year)
    monthly_revenue_fig = show_monthly_sales(selected_store, selected_year)
    
    return revenue_map_fig, weekly_revenue_fig, hourly_orders_fig, monthly_revenue_fig

@app.callback(
    [
        Output('scatterplot-revenue', 'figure'),
        Output('pizza-donut', 'figure'),
        Output('pizza-scatterplot', 'figure')
    ],
    [Input('url', 'pathname')]
)
def update_overview_charts(_):
    scatterplot_revenue_fig = create_scatter_plots()
    pizza_donut_fig = create_pizza_donut()
    pizza_scatter_plot_fig = create_pizza_scatter_plot()
    
    return scatterplot_revenue_fig, pizza_donut_fig, pizza_scatter_plot_fig

@app.callback(
    [
        Output('top-stores-2020', 'children'),
        Output('top-stores-2021', 'children'),
        Output('top-stores-2022', 'children'),
        Output('worst-stores-2020', 'children'),
        Output('worst-stores-2021', 'children'),
        Output('worst-stores-2022', 'children')
    ],
    [Input('global-year-dropdown', 'value')]
)
def update_stores_tables(selected_year):
    store_colors = {}
    color_generator = generate_colors()
    
    top_stores_2020, _ = create_top_stores_table(2020, store_colors, color_generator)
    top_stores_2021, _ = create_top_stores_table(2021, store_colors, color_generator)
    top_stores_2022, _ = create_top_stores_table(2022, store_colors, color_generator)
    
    worst_stores_2020, _ = create_worst_stores_table(2020, store_colors, color_generator)
    worst_stores_2021, _ = create_worst_stores_table(2021, store_colors, color_generator)
    worst_stores_2022, _ = create_worst_stores_table(2022, store_colors, color_generator)
    
    return top_stores_2020, top_stores_2021, top_stores_2022, worst_stores_2020, worst_stores_2021, worst_stores_2022

@app.callback(
    [
        Output('repeat-order', 'figure'),
        Output('rfm-scatter-chart', 'figure'),
        Output('aggregated-monetary-table', 'children')
    ],
    [
        Input('revenue-map', 'clickData'),
        Input('global-year-dropdown', 'value')
    ]
)
def update_customer_charts(click_data, selected_year):
    if not click_data or 'points' not in click_data:
        return [go.Figure(), go.Figure(), "No data"]
    
    selected_store = click_data['points'][0]['customdata'][0]
    
    repeat_order_fig = create_grouped_bar_chart(selected_store)
    rfm_scatter_fig = create_rfm_scatter_chart(selected_store)
    aggregated_monetary_table = create_aggregated_monetary_table(selected_store)
    
    return repeat_order_fig, rfm_scatter_fig, aggregated_monetary_table



    
if __name__ == '__main__':
    app.run_server(debug=True)
    
