import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import itertools
from branca.element import Template, MacroElement
from folium.plugins import HeatMap, HeatMapWithTime, MarkerCluster, Fullscreen

st.markdown("""
    <style>
    /* Multiselect customization */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #9c3675 !important;
    }
    .stMultiSelect [data-baseweb="tag"] div {
        color: white !important;
    }
    .stMultiSelect > div {
        border-color: #9c3675 !important;
    }

    /* Checkbox customization */
    input[type="checkbox"] + div svg {
        color: #9c3675 !important;
        stroke: #ffffff !important;
        fill: #9c3675 !important;
    }
    </style>
""", unsafe_allow_html=True)


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

df['municipio'] = df['municipio'].fillna("No Info")

# Prioritized termales
prioritized_df = load_data_termales()

# Split lat/lon from 'Georreferenciación'
lat_lon_split = prioritized_df["Georreferenciación"].str.split(",", expand=True)
prioritized_df["latitude"] = lat_lon_split[0].astype(float)
prioritized_df["longitude"] = lat_lon_split[1].astype(float)

# Verify structure after transformation
prioritized_df = prioritized_df[["Centro Termal", "Municipio", "Priorizado", "latitude", "longitude"]]
prioritized_df = prioritized_df.dropna(subset=['latitude'])

# Sidebar header
st.sidebar.image("datain/fontur_logo.png", width=180)
st.sidebar.markdown("----")

# Filtros geograficos
st.sidebar.title("Filtros geográficos")

# Corredor Filter
all_corredores = sorted(df['corredor'].dropna().unique())
selected_corredores = st.sidebar.multiselect(
    "Seleccione uno o más corredores:",
    options=all_corredores,
    default=all_corredores
)

# Municipality filter
all_municipios = sorted(df['municipio'].dropna().unique())
selected_municipios = st.sidebar.multiselect(
    "Seleccione uno o más municipios:",
    options=all_municipios,
    default=all_municipios
)

st.sidebar.markdown("----")
st.sidebar.title("Filtros de elementos del mapa")

# Toggles for layers
show_markers = st.sidebar.checkbox("Mostrar marcadores de puntos de interés", value=True)
show_heatmap = st.sidebar.checkbox("Mostrar mapa de calor", value=False)


# Selector de columnas
selected_columns = ['name', 'municipio', 'sub_category', 'types', 'average_rating', 'user_ratings_total', 'latitude', 'longitude']
#st.sidebar.subheader("Columnas a mostrar")
#all_columns = ['name', 'municipio', 'sub_category', 'types', 'average_rating', 'user_ratings_total', 'latitude', 'longitude']
#selected_columns = st.sidebar.multiselect(
#    "Seleccione columnas:",
#    options=all_columns,
#    default=all_columns
#)

st.sidebar.markdown("----")
st.sidebar.title("Filtros de tipos de lugares")

# Category 1 Filter
all_info_types = sorted(df['info_type'].dropna().unique())
selected_info_types = st.sidebar.multiselect(
    "Seleccione uno o más categorías:",
    options=all_info_types,
    default=all_info_types
)

# Category 1 Filter
all_categories_main = sorted(df['category'].dropna().unique())
selected_categories_main = st.sidebar.multiselect(
    "Seleccione una o más sub-categorías:",
    options=all_categories_main,
    default=all_categories_main
)

# Category 3 filter
all_categories = sorted(df['sub_category'].unique())
first_category = all_categories[0]

selected_categories = st.sidebar.multiselect(
    "Seleccione una o más tipos de lugares:",
    options=all_categories,
    default=[first_category]  # Only load the first one by default
)

st.sidebar.markdown("----")

# Filtered data
# Apply filters to the dataset
filtered_df = df[
    df['sub_category'].isin(selected_categories) &
    df['municipio'].isin(selected_municipios) &
    df['corredor'].isin(selected_corredores) &
    df['info_type'].isin(selected_info_types) &
    df['category'].isin(selected_categories_main)
]

# Assign colors to each subcategory
colors = itertools.cycle(["blue", "green", "red", "orange", "purple", "darkred", "cadetblue", "pink"])
color_map = {cat: next(colors) for cat in all_categories}

# Center of the map
if not filtered_df.empty and filtered_df[['latitude', 'longitude']].notnull().all().all():
    center_lat = filtered_df['latitude'].mean()
    center_lon = filtered_df['longitude'].mean()
else:
    # Coordenadas por defecto (Bogotá)
    center_lat = 4.7110
    center_lon = -74.0721

# Create folium map
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)

# Fullscreen
Fullscreen(
    position='topright',
    title='Pantalla completa',
    title_cancel='Salir de pantalla completa',
    force_separate_button=True
).add_to(m)


# Add a heatmap layer if enabled
if show_heatmap:
    heat_data = [[row['latitude'], row['longitude']] for _, row in filtered_df.iterrows()]
    heat_layer = folium.FeatureGroup(name="Mapa de Calor de POIs", show=True)
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
st.markdown("### Proyecto de Productos Turísticos de Termales")

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
st_data = st_folium(
    m,
    width="100%",      # Responsive width
    height=600,
    returned_objects=[],
    use_container_width=True
)



