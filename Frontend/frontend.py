import streamlit as st
import pandas as pd
import plotly.express as px

# Dummy-Daten für den Umsatz nach Standorten und Jahren
dummy_data = pd.DataFrame({
    'storeID': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    '2018': [5000, 4800, 4500, 4200, 4000, 3800, 3600, 3400, 3200, 3000],
    '2019': [5100, 4900, 4600, 4300, 4100, 3900, 3700, 3500, 3300, 3100],
    '2020': [5200, 5000, 4700, 4400, 4200, 4000, 3800, 3600, 3400, 3200],
    '2021': [5300, 5100, 4800, 4500, 4300, 4100, 3900, 3700, 3500, 3300],
    '2022': [5400, 5200, 4900, 4600, 4400, 4200, 4000, 3800, 3600, 3400],
})

# Dummy-Daten für Bestellungen
np.random.seed(42)
order_dates = pd.date_range(start='2022-01-01', end='2022-12-31', freq='D')
order_data = pd.DataFrame({
    'orderID': range(1, 101),
    'customerID': np.random.randint(1, 21, size=100),
    'orderDate': np.random.choice(order_dates, size=100)
})

# Dummy-Daten für wiederholte Bestellungen
repeat_orders_data = pd.DataFrame({
    'customerID': range(1, 21),
    'repeatOrders': np.random.randint(1, 11, size=20)
})

# Funktion zum Erstellen des Histogramms für wiederholte Bestellungen
def create_repeat_orders_histogram(repeat_orders_data):
    fig = px.histogram(repeat_orders_data, x='repeatOrders', title='Distribution of Repeat Orders per Customer',
                       labels={'repeatOrders': 'Number of Repeat Orders', 'count': 'Number of Customers'})
    fig.update_traces(marker_color='skyblue', marker_line_color='black', marker_line_width=1)
    fig.update_layout(xaxis_title='Number of Repeat Orders', yaxis_title='Number of Customers')
    return fig

# Funktion für das Haupt-Dashboard
def main():
    # Streamlit-Seitenkonfiguration
    st.set_page_config(
        page_title="Pizzeria Dashboard",
        page_icon="🍕",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Seitenleiste
    st.sidebar.image("images/CaptainPizza.png", width=170, use_column_width=False)
    st.sidebar.markdown("<h1 style='text-align: center; color: white; margin-left: -30px;'>🍕 Pizzeria Dashboard</h1>", unsafe_allow_html=True)

    # Filtermöglichkeiten
    view_option = st.sidebar.radio("Select your view:", ("Overview", "Regionview", "Storeview"))

    if view_option == "Overview":
        st.subheader("Overview")

        # Filteroptionen für Top 10 Standorte
        filter_option = st.selectbox("Revenue of the stores:", ("Top 10 best", "Top 10 badest"))

        if filter_option == "Top 10 best":
            top_10_best = dummy_data.nlargest(10, ['2018', '2019', '2020', '2021', '2022']).set_index('storeID')
            fig = px.bar(top_10_best.T, title='Top 10 best stores by revenue', labels={'index': 'Year', 'value': 'Revenue'}, width=800, height=500)
            st.plotly_chart(fig)
        else:
            top_10_worst = dummy_data.nsmallest(10, ['2018', '2019', '2020', '2021', '2022']).set_index('storeID')
            fig = px.bar(top_10_worst.T, title='Top 10 worst stores by revenue', labels={'index': 'Year', 'value': 'Revenue'}, width=800, height=500)
            st.plotly_chart(fig)

        # Benutzerdefinierte Auswahl der Geschäfte
        st.subheader("Select Store:")
        store_ids = st.multiselect("Store ID", dummy_data['storeID'])

        if store_ids:
            for store_id in store_ids:
                show_monthly_sales(store_id)

    # Visualisierung für Kundenloyalität und Wiederholungsbestellungen
    st.subheader("Customer Loyalty and Repeat Orders")
    st.write("This visualization shows the distribution of repeat orders per customer.")

    # Histogramm für wiederholte Bestellungen anzeigen
    st.subheader("Histogram of Repeat Orders per Customer")
    fig = create_repeat_orders_histogram(repeat_orders_data)
    st.plotly_chart(fig)

# Funktion zum Anzeigen der monatlichen Umsätze
def show_monthly_sales(store_id):
    st.subheader(f"Monthly Sales for Store {store_id}")
    monthly_sales_data = pd.DataFrame({
        'Month': range(1, 13),
        'Sales': np.random.randint(1000, 5000, size=12)  # Dummy-Daten für monatlichen Umsatz
    })
    fig = px.bar(monthly_sales_data, x='Month', y='Sales', title=f'Monthly Sales for Store {store_id}', labels={'Month': 'Month', 'Sales': 'Sales'})
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()