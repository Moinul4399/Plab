import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import plotly.express as px

# Datenbankverbindung einrichten
DATABASE_URL = 'postgresql+psycopg2://postgres:database123!@localhost/pizzadatabase'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def execute_query(query):
    with session.begin():
        result = session.execute(query)
        return result.fetchall()

# Hilfsfunktion zum sicheren Konvertieren in numerische Werte
def safe_to_numeric(series):
    try:
        return pd.to_numeric(series)
    except Exception:
        return series

@st.cache_data(ttl=600)
def get_top_stores():
    query = text("""
        SELECT
            s.storeid,
            s.zipcode,
            s.state_abbr,
            s.city,
            s.state,
            SUM(p.price) AS total_revenue
        FROM
            stores s
        JOIN
            orders o ON s.storeid = o.storeid
        JOIN
            orderitems oi ON o.orderid = oi.orderid
        JOIN
            products p ON oi.sku = p.sku
        GROUP BY
            s.storeid,
            s.zipcode,
            s.state_abbr,
            s.city,
            s.state
        ORDER BY
            total_revenue DESC
        LIMIT 10;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'zipcode': row[1], 'state_abbr': row[2], 'city': row[3], 'state': row[4], 'total_revenue': row[5]} for row in data]

@st.cache_data(ttl=600)
def get_customer_orders():
    query = text("""
        SELECT
            o.customerid,
            o.orderid,
            o.orderdate,
            SUM(p.price * oi.nitems) as total_amount
        FROM
            orders o
        JOIN
            orderitems oi ON o.orderid = oi.orderid
        JOIN
            products p ON oi.sku = p.sku
        GROUP BY
            o.customerid, o.orderid, o.orderdate
        ORDER BY
            o.customerid, o.orderdate;
    """)
    data = execute_query(query)
    return pd.DataFrame(data, columns=['customerid', 'orderid', 'orderdate', 'total_amount'])

#def calculate_rfm(df):
    # Konvertieren Sie das Datum in ein Datetime-Format
 #   df['orderdate'] = pd.to_datetime(df['orderdate'])
    
    # Konvertieren Sie die total_amount Spalte in float
  #  df['total_amount'] = df['total_amount'].astype(float)

    # Aktuelles Datum definieren
   # current_date = df['orderdate'].max() + pd.DateOffset(1)

    # Berechnen Sie die RFM-Werte
    #rfm = df.groupby('customerid').agg({
     #   'orderdate': lambda x: (current_date - x.max()).days,
      #  'orderid': 'count',
       # 'total_amount': 'sum'
    #}).reset_index()

    #rfm.columns = ['customerid', 'recency', 'frequency', 'monetary']

    # RFM-Score berechnen
  #  rfm['r_score'] = pd.qcut(rfm['recency'], 4, ['1', '2', '3', '4'])
   # rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, ['4', '3', '2', '1'])
    #rfm['m_score'] = pd.qcut(rfm['monetary'], 4, ['4', '3', '2', '1'])

    #rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
 #   return rfm

# Berechnung der RFM-Scores
#customer_orders = get_customer_orders()
#rfm_scores = calculate_rfm(customer_orders)

#def plot_rfm_segments(rfm_scores):
 #   fig = px.scatter(
  #      rfm_scores,
   #     x='recency',
    #    y='monetary',
     #   size='frequency',
      #  color='rfm_score',
       # hover_data=['customerid'],
        #title='RFM Segmentation',
        #labels={'recency': 'Recency (days)', 'frequency': 'Frequency', 'monetary': 'Monetary Value'}
    #)
    #st.plotly_chart(fig, use_container_width=True)


# RFM-Segmente plotten
#plot_rfm_segments(rfm_scores)'

@st.cache_data(ttl=600)
def store_locations():
    query = text("""
        SELECT city, AVG(latitude) AS avg_latitude, AVG(longitude) AS avg_longitude
        FROM stores
        GROUP BY city
        ORDER BY city;
    """)
    data = execute_query(query)
    return [{'city': row[0], 'avg_latitude': float(row[1]), 'avg_longitude': float(row[2])} for row in data]

@st.cache_data(ttl=600)
def customer_locations():
    query = text("""
        SELECT latitude, longitude
        FROM customers
        ORDER BY latitude, longitude;
    """)
    data = execute_query(query)
    return [{'latitude': row[0], 'longitude': row[1]} for row in data]

@st.cache_data(ttl=600)
def store_annual_revenues():
    query = text("""
        SELECT
            s.storeid,
            s.city,
            s.latitude,
            s.longitude,
            SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2018 THEN o.total ELSE 0 END) AS revenue_2018,
            SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2019 THEN o.total ELSE 0 END) AS revenue_2019,
            SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2020 THEN o.total ELSE 0 END) AS revenue_2020,
            SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2021 THEN o.total ELSE 0 END) AS revenue_2021,
            SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2022 THEN o.total ELSE 0 END) AS revenue_2022
        FROM
            stores s
        JOIN
            orders o ON s.storeid = o.storeid
        GROUP BY
            s.storeid, s.city, s.latitude, s.longitude
        ORDER BY
            s.city;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'city': row[1], 'latitude': row[2], 'longitude': row[3], 'revenue_2018': row[4], 'revenue_2019': row[5], 'revenue_2020': row[6], 'revenue_2021': row[7], 'revenue_2022': row[8]} for row in data]

@st.cache_data(ttl=600)
def get_store_data():
    revenue_query = text("""
        SELECT 
            stores.storeid,
            EXTRACT(YEAR FROM orders.orderdate) AS year,
            SUM(orders.nitems * products.price) AS revenue
        FROM 
            stores
        JOIN 
            orders ON stores.storeid = orders.storeid
        JOIN 
            orderitems ON orders.orderid = orderitems.orderid
        JOIN 
            products ON orderitems.sku = products.sku
        GROUP BY 
            stores.storeid, EXTRACT(YEAR FROM orders.orderdate)
        ORDER BY 
            stores.storeid, year;
    """)
    
    order_count_query = text("""
        SELECT
            stores.storeid,
            EXTRACT(YEAR FROM orders.orderdate) AS year,
            COUNT(DISTINCT orders.orderid) AS order_count  
        FROM
            stores
        JOIN
            orders ON stores.storeid = orders.storeid
        GROUP BY
            stores.storeid, EXTRACT(YEAR FROM orders.orderdate)
        ORDER BY
            stores.storeid, year;
    """)

    revenue_result = execute_query(revenue_query)
    order_count_result = execute_query(order_count_query)

    revenue_data = {(row[0], row[1]): row[2] for row in revenue_result}
    order_data = {(row[0], row[1]): row[2] for row in order_count_result}
    
    combined_data = []
    for (storeid, year), revenue in revenue_data.items():
        order_count = order_data.get((storeid, year), 0)
        combined_data.append({
            "storeid": storeid, 
            "year": year, 
            "revenue": revenue, 
            "order_count": order_count
        })

    return combined_data

@st.cache_data(ttl=600)
def get_metrics():
    total_customers_query = text("SELECT COUNT(*) FROM customers;")
    total_revenue_query = text("SELECT SUM(o.total) FROM orders o;")
    average_revenue_per_store_query = text("""
        SELECT AVG(total_revenue) FROM (
            SELECT SUM(o.total) AS total_revenue
            FROM orders o
            GROUP BY o.storeid
        ) AS store_revenues;
    """)
    new_customers_query = text("""
        WITH first_orders AS (
            SELECT 
                customerid, 
                MIN(orderdate) AS first_order_date
            FROM 
                orders
            GROUP BY 
                customerid
        ),
        customers_pre_2021 AS (
            SELECT 
                customerid
            FROM 
                first_orders
            WHERE 
                EXTRACT(YEAR FROM first_order_date) < 2021
        ),
        customers_2021 AS (
            SELECT 
                customerid
            FROM 
                first_orders
            WHERE 
                EXTRACT(YEAR FROM first_order_date) = 2021
        ),
        customers_2022 AS (
            SELECT 
                customerid
            FROM 
                first_orders
            WHERE 
                EXTRACT(YEAR FROM first_order_date) = 2022
        ),
        new_customers_2021 AS (
            SELECT 
                COUNT(DISTINCT customers_2021.customerid) AS count
            FROM 
                customers_2021
            LEFT JOIN 
                customers_pre_2021
            ON 
                customers_2021.customerid = customers_pre_2021.customerid
            WHERE 
                customers_pre_2021.customerid IS NULL
        ),
        new_customers_2022 AS (
            SELECT 
                COUNT(DISTINCT customers_2022.customerid) AS count
            FROM 
                customers_2022
            LEFT JOIN 
                customers_2021
            ON 
                customers_2022.customerid = customers_2021.customerid
            WHERE 
                customers_2021.customerid IS NULL
        )
        SELECT 
            new_customers_2021.count AS new_customers_2021,
            new_customers_2022.count AS new_customers_2022
        FROM 
            new_customers_2021, new_customers_2022;
    """)
    total_revenue_per_year_query = text("""
        SELECT 
            EXTRACT(YEAR FROM orderdate) AS year,
            SUM(total) AS total_revenue
        FROM 
            orders
        WHERE 
            EXTRACT(YEAR FROM orderdate) IN (2021, 2022)
        GROUP BY 
            year
        ORDER BY 
            year;
    """)
    average_revenue_per_store_per_year_query = text("""
        SELECT EXTRACT(YEAR FROM orderdate) AS Jahr, SUM(total) / 32 AS Durchschnittsumsatz_pro_Store
        FROM orders
        WHERE EXTRACT(YEAR FROM orderdate) IN (2021, 2022)
        GROUP BY EXTRACT(YEAR FROM orderdate)
        ORDER BY Jahr;
    """)

    total_customers_result = execute_query(total_customers_query)
    total_revenue_result = execute_query(total_revenue_query)
    average_revenue_per_store_result = execute_query(average_revenue_per_store_query)
    new_customers_result = execute_query(new_customers_query)
    total_revenue_per_year_result = execute_query(total_revenue_per_year_query)
    average_revenue_per_store_per_year_result = execute_query(average_revenue_per_store_per_year_query)

    total_customers = int(total_customers_result[0][0])
    total_revenue = float(total_revenue_result[0][0])
    average_revenue_per_store = float(average_revenue_per_store_result[0][0])
    new_customers_2021 = int(new_customers_result[0][0])
    new_customers_2022 = int(new_customers_result[0][1])

    total_revenue_per_year = {int(row[0]): float(row[1]) for row in total_revenue_per_year_result}
    average_revenue_per_store_per_year = {int(row[0]): float(row[1]) for row in average_revenue_per_store_per_year_result}

    total_revenue_2021 = total_revenue_per_year.get(2021, 1)
    total_revenue_2022 = total_revenue_per_year.get(2022, 1)
    total_revenue_change = (total_revenue_2022 - total_revenue_2021) / total_revenue_2021 * 100

    avg_revenue_per_store_2021 = average_revenue_per_store_per_year.get(2021, 1)
    avg_revenue_per_store_2022 = average_revenue_per_store_per_year.get(2022, 1)
    avg_revenue_per_store_change = (avg_revenue_per_store_2022 - avg_revenue_per_store_2021) / avg_revenue_per_store_2021 * 100

    new_customers_change = (new_customers_2022 - new_customers_2021) / new_customers_2021 * 100 if new_customers_2021 else 0

    return {
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'average_revenue_per_store': average_revenue_per_store,
        'new_customers_2021': new_customers_2021,
        'new_customers_2022': new_customers_2022,
        'total_revenue_2022': total_revenue_2022,
        'total_revenue_change': total_revenue_change,
        'avg_revenue_per_store_2022': avg_revenue_per_store_2022,
        'avg_revenue_per_store_change': avg_revenue_per_store_change,
        'new_customers_change': new_customers_change
    }

@st.cache_data(ttl=600)
def store_monthly_revenues():
    query = text("""
        SELECT
            s.storeid,
            s.city,
            s.latitude,
            s.longitude,
            to_char(o.orderdate, 'YYYY-MM') AS month,
            SUM(o.total) AS revenue
        FROM
            stores s
        JOIN
            orders o ON s.storeid = o.storeid
        GROUP BY
            s.storeid, s.city, s.latitude, s.longitude, to_char(o.orderdate, 'YYYY-MM')
        ORDER BY
            s.city, month;
    """)
    data = execute_query(query)

    monthly_revenues = {}
    for row in data:
        store_id, city, latitude, longitude, month, revenue = row

        if store_id not in monthly_revenues:
            monthly_revenues[store_id] = {
                'storeid': store_id,
                'city': city,
                'latitude': latitude,
                'longitude': longitude,
                'monthly_revenues': {}
            }
        monthly_revenues[store_id]['monthly_revenues'][month] = revenue

    return list(monthly_revenues.values())

@st.cache_data(ttl=600)
def pizza_orders():
    query = text("""
        SELECT
            p.category AS pizza_category,
            EXTRACT(YEAR FROM o.orderdate) AS order_year,
            COUNT(*) AS total_orders
        FROM
            orderitems oi
        JOIN
            products p ON oi.sku = p.sku
        JOIN
            orders o ON oi.orderid = o.orderid
        WHERE
            p.name LIKE '%Pizza%'
            AND EXTRACT(YEAR FROM o.orderdate) IN (2020, 2021, 2022)
        GROUP BY
            p.category, EXTRACT(YEAR FROM o.orderdate)
        ORDER BY
            order_year, total_orders DESC;
    """)
    data = execute_query(query)
    return [{'pizza_category': row[0], 'order_year': int(row[1]), 'total_orders': row[2]} for row in data]

@st.cache_data(ttl=600)
def top_5_stores():
    query = text("""
        WITH yearly_sales AS (
            SELECT
                storeid,
                EXTRACT(YEAR FROM orderdate) AS year,
                SUM(total) AS annual_sales
            FROM
                orders
            WHERE
                EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
            GROUP BY
                storeid,
                EXTRACT(YEAR FROM orderdate)
        )
        SELECT
            s.storeid,
            s.year,
            s.annual_sales
        FROM (
            SELECT
                storeid,
                year,
                annual_sales,
                ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales DESC) AS rank
            FROM
                yearly_sales
        ) s
        WHERE
            s.rank <= 5
        ORDER BY
            s.year,
            s.annual_sales DESC;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]

@st.cache_data(ttl=600)
def worst_5_stores():
    query = text("""
        WITH yearly_sales AS (
            SELECT
                storeid,
                EXTRACT(YEAR FROM orderdate) AS year,
                SUM(total) AS annual_sales
            FROM
                orders
            WHERE
                EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
            GROUP BY
                storeid,
                EXTRACT(YEAR FROM orderdate)
        )
        SELECT
            s.storeid,
            s.year,
            s.annual_sales
        FROM (
            SELECT
                storeid,
                year,
                annual_sales,
                ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales ASC) AS rank
            FROM
                yearly_sales
        ) s
        WHERE
            s.rank <= 5
        ORDER BY
            s.year,
            s.annual_sales ASC;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]

@st.cache_data(ttl=600)
def revenues_by_pizza_type_2022():
    query = text("""
        SELECT
            p.name AS pizza_name,
            SUM(count_oi * p.price) AS total_revenue
        FROM (
            SELECT 
                oi.sku, 
                COUNT(oi.sku) AS count_oi
            FROM 
                orderitems oi
            JOIN 
                orders o ON oi.orderid = o.orderid
            WHERE 
                EXTRACT(YEAR FROM o.orderdate) = 2022
            GROUP BY 
                oi.sku
        ) oi_summary
        JOIN 
            products p ON oi_summary.sku = p.sku
        GROUP BY
            p.name
        ORDER BY
            total_revenue DESC;
    """)
    data = execute_query(query)
    return [{'pizza_name': row[0], 'total_revenue': row[1]} for row in data]

@st.cache_data(ttl=600)
def store_yearly_avg_orders():
    query = text("""
        SELECT
            s.storeid,
            s.city, 
            EXTRACT(YEAR FROM o.orderdate) AS order_year,
            ROUND(COUNT(DISTINCT o.orderid)::numeric / COUNT(DISTINCT o.customerid)::numeric, 2) AS avg_orders_per_customer
        FROM stores s
        JOIN orders o ON s.storeid = o.storeid
        GROUP BY s.storeid, s.city, EXTRACT(YEAR FROM o.orderdate);
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'city': row[1], 'year': int(row[2]), 'avg_orders_per_customer': float(row[3])} for row in data]

@st.cache_data(ttl=600)
def scatterplot_data():
    query = text("""
        SELECT
            p.name AS pizza_name,
            p.size AS pizza_size,
            SUM(o.nitems) AS total_sold,
            SUM(o.nitems * p.price) AS total_revenue
        FROM products p
        JOIN orderitems oi ON p.sku = oi.sku
        JOIN orders o ON oi.orderid = o.orderid
        GROUP BY p.name, p.size;
    """)
    data = execute_query(query)
    return [{'pizza_name': row[0], 'pizza_size': row[1], 'total_sold': row[2], 'total_revenue': row[3]} for row in data]

@st.cache_data(ttl=600)
def store_orders_per_hour():
    query = text("""
        SELECT
            storeid,
            EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles')) AS order_hour,
            COUNT(*) AS total_orders_per_hour
        FROM
            orders
        GROUP BY
            storeid, EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles'))
        ORDER BY
            storeid, order_hour;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'order_hour': row[1], 'total_orders_per_hour': row[2]} for row in data]

@st.cache_data(ttl=600)
def revenue_per_weekday():
    query = text("""
        SELECT
            o.storeid,
            (EXTRACT(DOW FROM o.orderdate) + 6) % 7 AS order_day_of_week,
            SUM(o.total) AS total_revenue
        FROM
            orders o
        GROUP BY
            o.storeid,
            (EXTRACT(DOW FROM o.orderdate) + 6) % 7
        ORDER BY
            o.storeid, order_day_of_week;
    """)
    data = execute_query(query)
    return [{'storeid': row[0], 'order_day_of_week': row[1], 'total_revenue': row[2]} for row in data]

@st.cache_data(ttl=600)
def get_pizza_scatter_data():
    query = text("""
        SELECT
            p.name AS pizza_name,
            p.size AS pizza_size,
            SUM(o.nitems) AS total_sold,
            SUM(o.nitems * p.price) AS total_revenue
        FROM products p
        JOIN orderitems oi ON p.sku = oi.sku
        JOIN orders o ON oi.orderid = o.orderid
        GROUP BY p.name, p.size;
    """)
    data = execute_query(query)
    return [{
        'pizza_name': row[0],
        'pizza_size': row[1],
        'total_sold': row[2],
        'total_revenue': row[3]
    } for row in data]

# Frontend ab jetzt

def create_location_map():
    store_data = store_locations()
    customer_data = customer_locations()

    if store_data and customer_data:
        store_df = pd.DataFrame(store_data)
        customer_df = pd.DataFrame(customer_data)

        store_df['Type'] = 'Store'
        customer_df['Type'] = 'Customer'
        
        # Zuerst Kunden-Daten, dann Store-Daten, damit Stores oben angezeigt werden
        data = pd.concat([customer_df, store_df], ignore_index=True)

        fig = go.Figure()
        for type, details in zip(["Customer", "Store"], [{"color": "green", "size": 6}, {"color": "blue", "size": 15}]):
            df = data[data["Type"] == type]
            fig.add_trace(go.Scattergeo(
                lon=df['avg_longitude'] if type == 'Store' else df['longitude'],
                lat=df['avg_latitude'] if type == 'Store' else df['latitude'],
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
                font=dict(size=14),
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
                fitbounds="locations",
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig
    else:
        return go.Figure()

    
    
def create_scatter_plots():
    scatter_data = get_store_data()
    if scatter_data:
        df = pd.DataFrame(scatter_data)
        
        df.rename(columns={"storeid": "Store ID", "year": "Year", "order_count": "Orders", "revenue": "Revenue"}, inplace=True)

        # Konvertiere Orders und Revenue in numerische Werte
        df['Orders'] = df['Orders'].apply(safe_to_numeric).apply(lambda x: round(x))  # Auf ganze Zahlen runden
        df['Revenue'] = df['Revenue'].apply(safe_to_numeric).round(1)  # Auf eine Dezimalstelle runden

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
        st.error("Fehler beim Abrufen der Scatter-Plot-Daten")
        return None

def show_monthly_sales(store_id, year):
    monthly_data = store_monthly_revenues()
    
    store_data = next((item for item in monthly_data if item['storeid'] == store_id), None)
    
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

            fig = px.bar(monthly_sales_df, x='Month', y='Sales', 
                         title=f'Monthly Sales for Store {store_id} in {year}', 
                         labels={'Month': 'Month', 'Sales': 'Sales'})
            return fig
        else:
            st.error(f"Keine Daten für Store {store_id} im Jahr {year} verfügbar")
    else:
        st.error(f"Keine Daten für Store {store_id} verfügbar oder kein Jahr angegeben")
    return None

def create_sales_heatmap(selected_year):
    revenue_data = store_annual_revenues()
    if revenue_data:
        data = pd.DataFrame(revenue_data)
        data_year = data[['latitude', 'longitude', 'city', f'revenue_{selected_year}']].copy()
        data_year['Revenue'] = data_year[f'revenue_{selected_year}'].apply(safe_to_numeric)

        # Sortiere die Daten nach Umsatz in absteigender Reihenfolge
        data_year = data_year.sort_values(by='Revenue', ascending=False)

        fig = px.scatter_geo(
            data_year,
            lat='latitude',
            lon='longitude',
            hover_name='city',
            size='Revenue',
            color='city',
            size_max=30,
            projection='albers usa'  # Fokus auf die USA
        )

        fig.update_traces(hovertemplate='%{hovertext}<br>Revenue: %{marker.size:$,.0f}')

        # Set focus on a specific point (latitude and longitude)
        focus_lat = 37.7749  # Beispielkoordinate (San Francisco)
        focus_lon = -122.4194  # Beispielkoordinate (San Francisco)

        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            geo=dict(
                scope='north america',  # Beschränkt die Karte auf Nordamerika
                center=dict(lat=focus_lat, lon=focus_lon),  # Fokus auf eine bestimmte Stelle
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
                fitbounds="locations",  # Zoom anpassen, um alle Punkte einzuschließen
            )
        )
        return fig
    else:
        return px.scatter_geo()
    
def create_weekday_revenue_bar_chart(store_id):
    revenue_data = revenue_per_weekday()

    # Finden Sie Daten für den spezifischen Store
    store_revenue_data = [item for item in revenue_data if item['storeid'] == store_id]
    
    if not store_revenue_data:
        st.error(f"Keine Umsatzdaten für Store {store_id} verfügbar.")
        return
    
    # Erstellung des DataFrame
    df = pd.DataFrame(store_revenue_data)
    
    # Umwandlung der Werte in numerische Typen
    df['order_day_of_week'] = df['order_day_of_week'].apply(safe_to_numeric)
    df['total_revenue'] = df['total_revenue'].apply(safe_to_numeric)

    # Mapping von Wochentagen
    days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    df['Day'] = df['order_day_of_week'].map(days_map)

    # Sortiere die Wochentage in der richtigen Reihenfolge
    ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['Day'] = pd.Categorical(df['Day'], categories=ordered_days, ordered=True)

    # Überprüfen auf NaN-Werte oder andere unerwartete Daten
    if df['total_revenue'].isnull().any():
        st.error("Es gibt NaN-Werte in den Umsatzdaten")
        return

    # Balkendiagramm erstellen
    fig = px.bar(df, x='Day', y='total_revenue', title=f'Weekly Revenue for Store {store_id}', labels={'Day': 'Day of the Week', 'total_revenue': 'Total Revenue'})
    
    st.plotly_chart(fig, use_container_width=True)

def create_pizza_scatter_plot():
    scatter_data = get_pizza_scatter_data()

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
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Keine Daten verfügbar.")

def create_pizza_donut():
    donut_data = revenues_by_pizza_type_2022()

    if donut_data:
        df_pizza = pd.DataFrame(donut_data)

        # Erstellen des Donut-Diagramms
        fig = px.pie(df_pizza, values='total_revenue', names='pizza_name', hole=0.3, title='The data is based for 2022')
        fig.update_traces(
            textinfo='label', 
            hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Percentage: %{percent:.2%}'
        )

        # Anpassung des Layouts für größere Grafik
        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            height=550,  # Höhe der Grafik vergrößern
        )
        
        return fig
    else:
        return None

def pizza_orders_tab():
    st.header("Pizza Orders Table")
    
    # Daten direkt von der Datenbankfunktion abrufen
    pizza_order_data = pizza_orders()

    if pizza_order_data:
        df = pd.DataFrame(pizza_order_data)
        
        # Pivot-Tabelle erstellen
        df_pivot = df.pivot_table(
            index='pizza_category',
            columns='order_year',
            values='total_orders',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Sicherstellen, dass die Werte numerisch sind und Fehler explizit behandeln
        df_pivot = df_pivot.apply(safe_to_numeric)

        # Gesamtbestellungen hinzufügen
        df_pivot['Total Orders'] = df_pivot.iloc[:, 1:].sum(axis=1)
        
        # Spaltennamen anpassen
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={'pizza_category': 'Pizza Category', 2020: '2020 ', 2021: '2021 ', 2022: '2022 '})

        # Index-Spalte hinzufügen und bei 1 beginnen lassen
        df_pivot.index = df_pivot.index + 1
        df_pivot.index.name = "Index"

        # Daten in einer Tabelle anzeigen
        st.dataframe(df_pivot)
    else:
        st.write("No data available.")

def top_5_stores_tab():
    st.header("Top 5 Stores Table")
    
    # Daten direkt aus der Datenbankfunktion abrufen
    top_stores_data = top_5_stores()

    if top_stores_data:
        df = pd.DataFrame(top_stores_data)
        
        # Daten nach Jahr und Umsatz sortieren und gruppieren
        for year in [2020, 2021, 2022]:
            df_year = df[df['year'] == year].sort_values(by='annual_sales', ascending=False).head(5).reset_index(drop=True)
            df_year.index += 1  # Index bei 1 beginnen lassen
            df_year = df_year[['storeid', 'annual_sales']]
            df_year.columns = ['Store ID', 'Revenue']
            
            if not df_year.empty:
                st.subheader(f"Top 5 Stores in {year}")
                st.dataframe(df_year)
            else:
                st.write(f"No data available for {year}.")
    else:
        st.write("No data available.")

def worst_5_stores_tab():
    st.header("Worst 5 Stores Table")
    
    # Daten direkt aus der Datenbankfunktion abrufen
    worst_stores_data = worst_5_stores()

    if worst_stores_data:
        df = pd.DataFrame(worst_stores_data)
        
        # Daten nach Jahr und Umsatz sortieren und gruppieren
        for year in [2020, 2021, 2022]:
            df_year = df[df['year'] == year].sort_values(by='annual_sales', ascending=True).head(5).reset_index(drop=True)
            df_year.index += 1  # Index bei 1 beginnen lassen
            df_year = df_year[['storeid', 'annual_sales']]
            df_year.columns = ['Store ID', 'Revenue']
            
            if not df_year.empty:
                st.subheader(f"Worst 5 Stores in {year}")
                st.dataframe(df_year)
            else:
                st.write(f"No data available for {year}.")
    else:
        st.write("No data available.")

#def plot_rfm_segments(rfm_scores):
 #   fig = px.scatter(
  #      rfm_scores,
   #     x='recency',
    #    y='monetary',
     #   size='frequency',
      #  color='rfm_score',
       # hover_data=['customerid'],
        #title='RFM Segmentation',
        #labels={'recency': 'Recency (days)', 'frequency': 'Frequency', 'monetary': 'Monetary Value'}
    #)
    #st.plotly_chart(fig, use_container_width=True)

# RFM-Segmente plotten
#plot_rfm_segments(rfm_scores)

def storeview_dashboard():
    st.title("Storeview Dashboard")
    
    # Monthly Revenue anzeigen        
    st.header("Monthly Revenue for Store")
    store_options = [s['storeid'] for s in store_monthly_revenues()]

    if store_options:
        store_id = st.selectbox('Select a store ID', store_options)
        year = st.selectbox("Select a Year", ['2020', '2021', '2022'])

        if store_id and year:
            fig_monthly_sales = show_monthly_sales(store_id, year)
            if fig_monthly_sales:
                st.plotly_chart(fig_monthly_sales, use_container_width=True)

def overview_dashboard():
    # Daten für Metriken abrufen
    
    metrics = get_metrics()
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "Location Map", "Store Revenue Map", "Weekly Revenue", 
        "Scatter Plots", "Pizza Sales Scatter Plot", "Pizza Art & Size", 
        "Pizza Orders Table", "Top 5 Stores Revenue", "Worst 5 Stores Revenue"
    ])
    
    #with tab1:
        #st.header("Location Map for Customers and Stores")
        #fig_location_map = create_location_map()
        #st.plotly_chart(fig_location_map, use_container_width=True)

    with tab2:
        st.header("Store Revenue Map")
        selected_year = st.selectbox('Select Year', ['2020', '2021', '2022'], key='year_filter')
        fig_sales_heatmap = create_sales_heatmap(selected_year)
        st.plotly_chart(fig_sales_heatmap, use_container_width=True)

    with tab3:
        st.header("Weekday Revenue")
        store_options = [s['storeid'] for s in store_monthly_revenues()]
        selected_storeW = st.selectbox("Select Store ID", store_options, key='weekday_revenue_store')
        if selected_storeW:
            create_weekday_revenue_bar_chart(selected_storeW)

    with tab4:
        st.header("Scatter Plots of Orders vs Revenue")
        fig_scatter_plots = create_scatter_plots()
        if fig_scatter_plots:
            st.plotly_chart(fig_scatter_plots, use_container_width=True)
        else:
            st.error("Fehler beim Abrufen der Scatter Plot Daten")
            
    with tab5:
        st.header("Pizza Sales and Revenue Scatter Plot")
        fig_pizza_scatter_plot = create_pizza_scatter_plot()
        if fig_pizza_scatter_plot:
            st.plotly_chart(fig_pizza_scatter_plot, use_container_width=True)
        else:
            st.error("Error fetching pizza scatter plot data")
            
    with tab6:
        st.header("Pizza Art & Size")
        pizza_chart = create_pizza_donut()
        st.plotly_chart(pizza_chart, use_container_width=True)
        
    with tab7:
        pizza_orders_tab()

    with tab8:
        top_5_stores_tab()
        
    with tab9:
        worst_5_stores_tab()

    #tab10, = st.tabs(["RFM Analysis"])

    #with tab10:
     #   st.header("RFM Analysis of Customer Behavior")
      #  plot_rfm_segments(rfm_scores)


def main():
    st.set_page_config(page_title="Pizzeria Dashboard", page_icon="🍕", layout="wide")

    # Sidebar mit Navigation
    page = st.sidebar.selectbox("Navigation", ["Overview", "Storeview"])

    if page == "Overview":
        overview_dashboard()
    elif page == "Storeview":
        storeview_dashboard()

if __name__ == "__main__":
    main()
