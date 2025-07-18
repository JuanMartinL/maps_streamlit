import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import itertools
from branca.element import Template, MacroElement
from folium.plugins import HeatMap, Fullscreen
from PIL import Image
import base64
from io import BytesIO

# --- Custom Styles ---
st.markdown("""
    <style>
    /* Multiselect customization */
    .stMultiSelect [data-baseweb=\"tag\"] {
        background-color: #9c3675 !important;
    }
    .stMultiSelect [data-baseweb=\"tag\"] div {
        color: white !important;
    }
    .stMultiSelect > div {
        border-color: #9c3675 !important;
    }

    /* Checkbox customization */
    input[type=\"checkbox\"] + div svg {
        color: #9c3675 !important;
        stroke: #ffffff !important;
        fill: #9c3675 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Logos ---
mincit_logo = Image.open("assets/logo_mincit_fontur.jpeg")
icon_datad = Image.open("assets/datad_logo.jpeg")  
buffered = BytesIO()
icon_datad.save(buffered, format="PNG")
icon_base64 = base64.b64encode(buffered.getvalue()).decode()

# --- Sidebar Logos ---
with st.sidebar:
    st.markdown("""
        <style>
            .logo-container img {
                margin: 0px !important;
                padding: 0px !important;
                background: none !important;
                border-radius: 0px !important;
                box-shadow: none !important;
            }
            .css-1v0mbdj.e115fcil1 {
                padding-top: 0rem;
                padding-bottom: 0rem;
            }
            .powered-container {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 8px;
                margin-top: -10px;
                font-size: 11px;
                color: grey;
            }
            .powered-container img {
                height: 45px;
                width: 45px;
                margin-bottom: -2px;
                border-radius: 50%;
                object-fit: cover;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class=\"logo-container\">', unsafe_allow_html=True)
    st.image(mincit_logo, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class=\"powered-container\">
            <img src=\"data:image/png;base64,{icon_base64}\" />
            <span>Powered by DataD</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Icon mapping per sub_category ---
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

# --- Data Loading ---
@st.cache_data
def load_data():
    return pd.read_csv("datain/map_data.csv")

def load_data_termales():
    return pd.read_csv("datain/termales_priorizados.csv", encoding='ISO-8859-1')

# Load datasets
df = load_data()
prioritized_df = load_data_termales()

# Clean df
for col in ['average_rating', 'user_ratings_total', 'municipio']:
    if col == 'average_rating':
        df[col] = df[col].fillna("No Info").astype(str)
    elif col == 'user_ratings_total':
        df[col] = df[col].fillna(0).astype(int)
    else:
        df[col] = df[col].fillna("No Info")

# Transform prioritized_df
lat_lon = prioritized_df['Georreferenciación'].str.split(',', expand=True)
prioritized_df['latitude'] = lat_lon[0].astype(float)
prioritized_df['longitude'] = lat_lon[1].astype(float)
prioritized_df = prioritized_df[['Centro Termal','Municipio','Priorizado','latitude','longitude']].dropna(subset=['latitude'])

# --- Sidebar Filters ---
st.sidebar.markdown("----")
st.sidebar.title("Filtros Geográficos")

# Corredor ➔ Municipio dependency
all_corredores = sorted(df['corredor'].dropna().unique())
selected_corredores = st.sidebar.multiselect("Seleccione uno o más corredores:", all_corredores, default=[])
filtered_corr = df[df['corredor'].isin(selected_corredores)] if selected_corredores else df
available_municipios = sorted(filtered_corr['municipio'].dropna().unique())
selected_municipios = st.sidebar.multiselect("Seleccione uno o más municipios:", available_municipios, default=[])

st.sidebar.markdown("----")
st.sidebar.title("Filtros de elementos del mapa")

# info_type ➔ category ➔ sub_category cascade
all_info_types = sorted(df['info_type'].dropna().unique())
selected_info_types = st.sidebar.multiselect("Seleccione uno o más tipos de información:", all_info_types, default=[])
filtered_info = df[df['info_type'].isin(selected_info_types)] if selected_info_types else df
available_categories = sorted(filtered_info['category'].dropna().unique())
selected_categories = st.sidebar.multiselect("Seleccione una o más categorías:", available_categories, default=[])
filtered_cat = filtered_info[filtered_info['category'].isin(selected_categories)] if selected_categories else filtered_info
available_sub = sorted(filtered_cat['sub_category'].dropna().unique())
selected_sub = st.sidebar.multiselect("Seleccione uno o más tipos de lugar:", available_sub, default=[])

# Layer toggles
st.sidebar.markdown("----")
show_markers = st.sidebar.checkbox("Mostrar marcadores", value=True)
show_heatmap = st.sidebar.checkbox("Mostrar mapa de calor", value=False)

# --- Apply Filters ---
filtered_df = df.copy()
if selected_corredores:
    filtered_df = filtered_df[filtered_df['corredor'].isin(selected_corredores)]
if selected_municipios:
    filtered_df = filtered_df[filtered_df['municipio'].isin(selected_municipios)]
if selected_info_types:
    filtered_df = filtered_df[filtered_df['info_type'].isin(selected_info_types)]
if selected_categories:
    filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
if selected_sub:
    filtered_df = filtered_df[filtered_df['sub_category'].isin(selected_sub)]

# --- Main Page ---
st.title("Mapa interactivo de lugares turísticos en municipios priorizados")
st.markdown("Seleccione filtros para visualizar los datos en el mapa.")

if not filtered_df.empty:
    # Assign colors dynamically
    colors = itertools.cycle(["blue","green","red","orange","purple","darkred","cadetblue","pink"])
    color_map = {cat: next(colors) for cat in available_sub}

    # Center map
    center_lat = filtered_df['latitude'].mean()
    center_lon = filtered_df['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)
    Fullscreen(position='topright', title='Pantalla completa', title_cancel='Salir', force_separate_button=True).add_to(m)

    # Heatmap layer
    if show_heatmap:
        heat_data = [[r['latitude'], r['longitude']] for _, r in filtered_df.iterrows()]
        HeatMap(heat_data, radius=12, blur=15, max_zoom=12).add_to(m)

    # Markers layer
    if show_markers:
        for _, row in filtered_df.iterrows():
            icon_name, color = icon_map.get(row['sub_category'], ("map-marker","gray"))
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=f"<b>{row['name']}</b><br>Municipio: {row['municipio']}<br>Tipo: {row['sub_category']}<br>Rating: {row['average_rating']} ({row['user_ratings_total']} reviews)<br><a href='{row['place_link']}' target='_blank'>Ver en Google</a>",
                icon=folium.Icon(icon=icon_name, color=color, prefix="fa")
            ).add_to(m)

    # Prioritized hot springs
    for _, row in prioritized_df.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"<b>{row['Centro Termal']}</b><br>Municipio: {row['Municipio']}<br>Priorizado: {row['Priorizado']}",
            icon=folium.Icon(color='darkpurple', icon='water', prefix='fa')
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width="100%", height=600)

    # Data table & download
    st.markdown("### Tabla de datos filtrados")
    cols = ['name','municipio','sub_category','types','average_rating','user_ratings_total','latitude','longitude']
    table = filtered_df[cols].sort_values(by='average_rating', ascending=False)
    st.dataframe(table, use_container_width=True)
    csv = table.to_csv(index=False)
    st.download_button("Descargar CSV", data=csv, file_name="datos_filtrados.csv", mime="text/csv")
else:
    st.info("No hay datos que mostrar. Seleccione filtros para cargar el mapa y la tabla.")
