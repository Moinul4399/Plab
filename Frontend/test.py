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
    #st.sidebar.image("images/CaptainPizza.png", width=170, use_column_width=False)
    st.sidebar.markdown("<h1 style='text-align: center; color: white; margin-left: -30px;'>🍕 Pizzeria Dashboard</h1>", unsafe_allow_html=True)

    # API-Endpunkt für Top-Stores-Daten
    api_url = "http://localhost:5000/api/top_stores"

    # Daten von der API abrufen
    top_stores_data = fetch_data(api_url)

    if top_stores_data and 'top_stores' in top_stores_data:
        top_stores_df = pd.DataFrame(top_stores_data['top_stores'])

        # Session-State initialisieren, um den Index der aktuellen Anzeige zu verfolgen
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0

        # Funktion zum Anzeigen des Diagramms basierend auf dem Index
        def display_chart(index):
            store_data = top_stores_df.iloc[index]
            store_id = store_data['storeID']
            store_revenue = store_data['total_revenue']
            store_city = store_data['city']
            
            fig = px.bar(top_stores_df[top_stores_df['storeID'] == store_id], 
                         x='storeID', 
                         y='total_revenue', 
                         color='city', 
                         title=f"Umsatz für Filiale {store_id} in {store_city}")
            fig.update_traces(marker=dict(color='blue'))  # Standardfarbe setzen
            fig.update_layout(clickmode='event+select')
            st.plotly_chart(fig)

            # Ereignis für Balkenklick
            def on_click(trace, points, selector):
                if points.point_inds:
                    selected_index = points.point_inds[0]
                    selected_store = top_stores_df.iloc[selected_index]
                    selected_store_id = selected_store['storeID']
                    selected_store_city = selected_store['city']
                    selected_store_monthly_data = fetch_monthly_data(selected_store_id)
                    display_monthly_chart(selected_store_id, selected_store_city, selected_store_monthly_data)

            fig.on_click(on_click)

        # Funktion zum Anzeigen der aktuellen Ansicht
        def display_current_view():
            if st.session_state.current_index == 0:
                st.write("Umsätze aller Stores")
                display_chart(st.session_state.current_index)
            else:
                st.write("Top-Stores basierend auf dem Umsatz")
                st.dataframe(top_stores_df)

        # Funktion zum Anzeigen des monatlichen Diagramms für einen bestimmten Store
        def display_monthly_chart(store_id, store_city, monthly_data):
            if monthly_data is not None:
                monthly_df = pd.DataFrame(monthly_data)
                fig = px.bar(monthly_df, x='month', y='monthly_revenue', title=f"Monatlicher Umsatz für Filiale {store_id} in {store_city}")
                st.plotly_chart(fig)

        # Funktion zum Abrufen der monatlichen Umsatzdaten für einen bestimmten Store
        def fetch_monthly_data(store_id):
            # Hier die Logik zum Abrufen der monatlichen Umsatzdaten implementieren
            # Zum Beispiel eine SQL-Abfrage an die Datenbank senden
            pass

        # Aktuelle Ansicht anzeigen
        display_current_view()

        # Karussell-Steuerelemente
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button('◀️ Vorherige'):
                st.session_state.current_index = (st.session_state.current_index - 1) % 2
        with col3:
            if st.button('Nächste ▶️'):
                st.session_state.current_index = (st.session_state.current_index + 1) % 2

    else:
        st.write("Keine Daten verfügbar oder Fehler beim Abrufen der Daten.")

if __name__ == "__main__":
    main()
