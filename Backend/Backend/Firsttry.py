import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Funktion zum Abrufen von Daten aus der API
def fetch_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Fehler beim Abrufen der Daten: Statuscode {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
        return None

# Hauptfunktion für das Dashboard
def main():
    # Streamlit-Seitenkonfiguration
    st.set_page_config(
        page_title="Pizzeria Dashboard",
        page_icon="🍕",
        layout="wide"
    )

    # Sidebar
    st.sidebar.markdown("<h1 style='text-align: center; color: white; margin-left: -30px;'>🍕 Pizzeria Dashboard</h1>", unsafe_allow_html=True)

    # API-Endpunkt für Top-Stores-Daten
    api_url_top_stores = "http://localhost:5000/api/top_stores"

    # Daten von der API abrufen
    top_stores_data = fetch_data(api_url_top_stores)

    if top_stores_data and 'top_stores' in top_stores_data:
        top_stores_df = pd.DataFrame(top_stores_data['top_stores'])

        # Diagramm für die Gesamtumsätze aller Stores erstellen
        fig_total_revenue = px.bar(top_stores_df, x='storeID', y='total_revenue', color='city', title="Gesamtumsätze aller Stores")
        st.plotly_chart(fig_total_revenue)

        # Karussell-Steuerelemente
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button('◀️ Vorherige'):
                pass  # Hier könnte Logik für vorherige Ansicht hinzugefügt werden
        with col3:
            if st.button('Nächste ▶️'):
                # Tabelle mit den Top-Stores anzeigen
                st.write("Top-Stores basierend auf dem Umsatz")
                st.dataframe(top_stores_df)

        # Diagramm für den monatlichen Umsatz eines ausgewählten Stores anzeigen
        selected_storeID = st.selectbox("Wähle einen Store aus:", top_stores_df['storeID'].unique())
        api_url_monthly_revenue = f"http://localhost:5000/api/monthly_revenue/{selected_storeID}"
        monthly_revenue_data = fetch_data(api_url_monthly_revenue)

        if monthly_revenue_data:
            monthly_revenue_df = pd.DataFrame(monthly_revenue_data)
            fig_monthly_revenue = px.bar(monthly_revenue_df, x='month', y='monthly_revenue', title=f"Monatlicher Umsatz für Store {selected_storeID}")
            st.plotly_chart(fig_monthly_revenue)

    else:
        st.write("Keine Daten verfügbar oder Fehler beim Abrufen der Daten.")

if __name__ == "__main__":
    main()
