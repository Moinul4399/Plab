import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np




# Funktion zum Erstellen der Umsatz-Heatmap
def create_location_map(data):
    fig = go.Figure()

    for type, color in zip(["Store", "Customer"], ["red", "green"]):
        df = data[data["Type"] == type]
        fig.add_trace(go.Scattergeo(
            lon=df['Longitude'],
            lat=df['Latitude'],
            text=df['Location'] + ' (' + df['Type'] + ')',  # Anpassung des Hover-Texts
            marker=dict(
                size=10,
                color=color,
                line=dict(width=1, color='rgba(0,0,0,0)')
            ),
            hovertemplate='%{text}<extra></extra>',  # Koordinaten ausblenden, nur Text anzeigen
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
            scope='usa',  # Kartenbereich auf USA beschränken
            projection_type='albers usa',
            showland=True,
            landcolor="rgb(217, 217, 217)",
            subunitcolor="rgb(255, 255, 255)",
            subunitwidth=0.5,
        ),
        margin={"r":0,"t":0,"l":0,"b":0}  # Margins entfernt, um Versatz zu verhindern
    )

    return fig

# Hauptfunktion für das Dashboard
def main():
    st.set_page_config(page_title="Pizzeria Dashboard", page_icon="🍕", layout="wide")

    # Dummy-Daten laden
    location_data = get_dummy_location_data()

    # Location Map
    st.header("Location Map for Customers and Stores")
    fig_location_map = create_location_map(location_data)
    st.plotly_chart(fig_location_map, use_container_width=True)

if _name_ == "_main_":
    main()