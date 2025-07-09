import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import itertools


# Load your cleaned dataset
@st.cache_data
def load_data():
    return pd.read_csv("map_data.csv")

df = load_data()

# Sidebar filter
st.sidebar.title("🎯 Filtros")
all_categories = sorted(df['sub_category'].unique())
selected_categories = st.sidebar.multiselect(
    "Seleccione una o más categorías:",
    options=all_categories,
    default=all_categories
)

# Selector de columnas
st.sidebar.markdown("----")
st.sidebar.subheader("📌 Columnas a mostrar")
all_columns = ['name', 'municipio', 'sub_category', 'types', 'average_rating', 'user_ratings_total', 'latitude', 'longitude']
selected_columns = st.sidebar.multiselect(
    "Seleccione columnas:",
    options=all_columns,
    default=all_columns
)


# Filtered data
filtered_df = df[df['sub_category'].isin(selected_categories)]

# Assign colors to each subcategory
colors = itertools.cycle(["blue", "green", "red", "orange", "purple", "darkred", "cadetblue", "pink"])
color_map = {cat: next(colors) for cat in all_categories}

# Center of the map
center_lat = filtered_df['latitude'].mean()
center_lon = filtered_df['longitude'].mean()

# Create folium map
m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

# Add markers
for _, row in filtered_df.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"""
                <b>{row['name']}</b><br>
                Municipio: {row['municipio']}<br>
                Subcategoría: {row['sub_category']}<br>
                """,
        icon=folium.Icon(color=color_map.get(row['sub_category'], "gray"))
    ).add_to(m)

# Display
st.title("Mapa interactivo de lugares turísticos en municipios priorizados")
st.markdown("Este mapa muestra lugares de interés relacionados con infraestructura turística alrededor de aguas termales. Use los filtros a la izquierda para explorar.")
st_data = st_folium(m, width=800, height=600)

# Interactive data table
st.markdown("### Tabla de datos filtrados")
sorted_df = filtered_df[selected_columns].sort_values(by='average_rating', ascending=False)
st.dataframe(sorted_df, use_container_width=True)


# Botón de descarga
csv = sorted_df.to_csv(index=False)
st.download_button(
    label="Descargar datos filtrados (CSV)",
    data=csv,
    file_name="datos_filtrados_termales.csv",
    mime="text/csv"
)