import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import itertools
from branca.element import Template, MacroElement
from folium.plugins import HeatMap, HeatMapWithTime, MarkerCluster, Fullscreen

# Icon mapping per sub_category
icon_map = {
    "Turismo Termal y Balnearios": ("spa", "green"),
    "Restaurantes": ("utensils", "blue"),
    "Agencias de viaje y guías": ("suitcase", "purple"),
    "Transporte turístico": ("bus", "orange"),
    "Culturales": ("landmark", "cadetblue"),
    "Tratamientos y terapias de relajación": ("heartbeat", "pink"),
    "Terapias alternativas y holísticas": ("leaf", "darkgreen"),
    "Espiritual y Ancestral": ("place-of-worship", "lightgray"),
    "Retiros": ("peace", "darkblue"),
    "Salud": ("medkit", "lightred"),
    "Financieros": ("money-bill", "gray"),
    "Transporte Público": ("subway", "lightblue"),
    "Peajes": ("road", "lightgray"),
    "Estaciones de servicio": ("gas-pump", "black"),
    "Naturaleza y Montaña": ("mountain", "darkgreen"),
    "Naturaleza & Montaña": ("mountain", "darkgreen"),
    "Caficultura": ("coffee", "brown"),
    "Artesanías y oficios": ("palette", "orange"),
    "Agroturismo": ("tractor", "green"),
    "Cultura y Comunidad": ("users", "purple"),
    "Alojamiento": ("bed", "darkred"),
    "Naturales": ("tree", "green"),
    "Arqueología y fósiles": ("university", "gray"),
    "Patrimonio colonial": ("archway", "black"),
    "Cultura ancestral": ("book", "darkpurple"),
    "Biodiversidad y selva": ("leaf", "darkgreen"),
    "Arquitectura simbólica": ("building", "gray"),
    "Naturaleza Extrema": ("bolt", "red")
}


# Load your cleaned dataset
@st.cache_data
def load_data():
    return pd.read_csv("datain/map_data.csv")
def load_data_termales():
    return pd.read_csv("datain/termales_priorizados.csv", encoding='ISO-8859-1')

# Scraped data
df = load_data()

# Replacing NAs
df['average_rating'] = df['average_rating'].astype(str)
df['average_rating'] = df['average_rating'].fillna("No Info")

df['user_ratings_total'] = df['user_ratings_total'].fillna(0)
df['user_ratings_total'] = df['user_ratings_total'].astype(int)

# Prioritized termales
prioritized_df = load_data_termales()

# Split lat/lon from 'Georreferenciación'
lat_lon_split = prioritized_df["Georreferenciación"].str.split(",", expand=True)
prioritized_df["latitude"] = lat_lon_split[0].astype(float)
prioritized_df["longitude"] = lat_lon_split[1].astype(float)

# Verify structure after transformation
prioritized_df = prioritized_df[["Centro Termal", "Municipio", "Priorizado", "latitude", "longitude"]]
prioritized_df = prioritized_df.dropna(subset=['latitude'])

# Sidebar filter
st.sidebar.title("Filtros")
all_categories = sorted(df['sub_category'].unique())
first_category = all_categories[0]

selected_categories = st.sidebar.multiselect(
    "Seleccione una o más categorías:",
    options=all_categories,
    default=[first_category]  # Only load the first one by default
)

# Selector de columnas
st.sidebar.markdown("----")
st.sidebar.subheader("Columnas a mostrar")
all_columns = ['name', 'municipio', 'sub_category', 'types', 'average_rating', 'user_ratings_total', 'latitude', 'longitude']
selected_columns = st.sidebar.multiselect(
    "Seleccione columnas:",
    options=all_columns,
    default=all_columns
)

# Marker toggle
show_markers = st.sidebar.checkbox("Mostrar marcadores de puntos de interés", value=True)

# Filtered data
filtered_df = df[df['sub_category'].isin(selected_categories)]

# Assign colors to each subcategory
colors = itertools.cycle(["blue", "green", "red", "orange", "purple", "darkred", "cadetblue", "pink"])
color_map = {cat: next(colors) for cat in all_categories}

# Center of the map
center_lat = filtered_df['latitude'].mean()
center_lon = filtered_df['longitude'].mean()

# Create folium map
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)

# Fullscreen
Fullscreen(
    position='topright',
    title='Pantalla completa',
    title_cancel='Salir de pantalla completa',
    force_separate_button=True
).add_to(m)


# Add a heatmap layer as a toggle
heat_data = [[row['latitude'], row['longitude']] for _, row in filtered_df.iterrows()]
heat_layer = folium.FeatureGroup(name="Mapa de Calor de POIs", show=False)
HeatMap(heat_data, radius=12, blur=15, max_zoom=12).add_to(heat_layer)
heat_layer.add_to(m)

# Add markers
if show_markers:
    for _, row in filtered_df.iterrows():
        icon_name, color = icon_map.get(row['sub_category'], ("map-marker", "gray"))
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"""
                <b>{row['name']}</b><br>
                Municipio: {row['municipio']}<br>
                Tipo de lugar: {row['sub_category']}<br>
                Tipo: {row['types']}<br>
                Calificación promedio: {row['average_rating']} ({int(row['user_ratings_total'])} reviews)<br>
                Enlace Google: {row['place_link']}
            """,
            icon=folium.Icon(icon=icon_name, color=color, prefix="fa")
        ).add_to(m)

# Hot Springs
for _, row in prioritized_df.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"""
            <b>{row['Centro Termal']}</b><br>
            Municipio: {row['Municipio']}<br>
            Priorizado: {row['Priorizado']}
        """,
        icon=folium.Icon(color='darkpurple', icon='water', prefix='fa')
    ).add_to(m)



# Display
st.title("Mapa interactivo de lugares turísticos en municipios priorizados")
st.markdown("# Proyecto de Productos Turísticos de Termales")

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

# Display
st.markdown("Este mapa muestra lugares de interés relacionados con infraestructura turística alrededor de aguas termales. Use los filtros a la izquierda para explorar.")
folium.LayerControl(collapsed=False).add_to(m)
st_data = st_folium(m, width=800, height=600)



