import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import itertools
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
        .logo-container img { margin:0; padding:0; background:none; border-radius:0; box-shadow:none; }
        .powered-container { display:flex; justify-content:center; align-items:center; gap:8px; margin-top:-10px; font-size:11px; color:grey; }
        .powered-container img { height:45px; width:45px; border-radius:50%; object-fit:cover; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class=\"logo-container\">', unsafe_allow_html=True)
    st.image(mincit_logo, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class=\"powered-container\">
        <img src=\"data:image/png;base64,{icon_base64}\" />
        <span>Powered by DataD</span>
    </div>
    """, unsafe_allow_html=True)

# --- Icon mapping ---
icon_map = {
    "Turismo Termal y Balnearios": ("spa","green"), "Restaurantes": ("utensils","blue"),
    # ... other icons ...
}

# --- Data Loading ---
@st.cache_data
def load_data():
    return pd.read_csv("datain/map_data.csv")
def load_termales():
    return pd.read_csv("datain/termales_priorizados.csv", encoding='ISO-8859-1')

df = load_data()
termales = load_termales()
# Clean df
for c in ['average_rating','user_ratings_total','municipio']:
    if c=='average_rating': df[c]=df[c].fillna('No Info').astype(str)
    elif c=='user_ratings_total': df[c]=df[c].fillna(0).astype(int)
    else: df[c]=df[c].fillna('No Info')
# Termales transform
latlon=termales['Georreferenciación'].str.split(',',expand=True)
termales['latitude']=latlon[0].astype(float)
termales['longitude']=latlon[1].astype(float)
termales=termales[['Centro Termal','Municipio','Priorizado','latitude','longitude']].dropna(subset=['latitude'])

# --- Sidebar Filters Sequence ---
st.sidebar.title('Filtros Geográficos y de Contenido')

# 1. Corredor
all_corr = sorted(df['corredor'].dropna().unique())
selected_corr = st.sidebar.multiselect('Seleccione uno o más corredores', all_corr, default=[])

# 2. Municipio: appears only if corredor selected
if selected_corr:
    df_corr = df[df['corredor'].isin(selected_corr)]
    all_mun = sorted(df_corr['municipio'].dropna().unique())
    selected_mun = st.sidebar.multiselect('Seleccione municipios', all_mun, default=all_mun)
else:
    selected_mun = []

# 3. info_type: appears after municipios
if selected_mun:
    all_info = sorted(df[df['municipio'].isin(selected_mun)]['info_type'].dropna().unique())
    selected_info = st.sidebar.multiselect('Seleccione tipos de información', all_info, default=[])
else:
    selected_info = []

# 4. Category & sub_category cascade only after info_type
if selected_info:
    df_info = df[df['info_type'].isin(selected_info)]
    cats = sorted(df_info['category'].dropna().unique())
    sel_cats = st.sidebar.multiselect('Seleccione categorías', cats, default=[])
    df_cat = df_info[df_info['category'].isin(sel_cats)] if sel_cats else df_info
    subs = sorted(df_cat['sub_category'].dropna().unique())
    sel_sub = st.sidebar.multiselect('Seleccione tipos de lugar', subs, default=[])
else:
    sel_cats=[]; sel_sub=[]

# Layer toggles always visible
st.sidebar.markdown('----')
show_markers = st.sidebar.checkbox('Mostrar marcadores', True)
show_heatmap = st.sidebar.checkbox('Mostrar mapa de calor', False)

# --- Apply Filters ---
fdf = df.copy()
if selected_corr: fdf=fdf[fdf['corredor'].isin(selected_corr)]
if selected_mun:   fdf=fdf[fdf['municipio'].isin(selected_mun)]
if selected_info:  fdf=fdf[fdf['info_type'].isin(selected_info)]
if sel_cats:       fdf=fdf[fdf['category'].isin(sel_cats)]
if sel_sub:        fdf=fdf[fdf['sub_category'].isin(sel_sub)]

# Show map only after info_type
st.title('Mapa interactivo de productos turísticos')
st.markdown('Use los filtros en secuencia: corredor → municipios → info_type para mostrar datos.')

if selected_info and not fdf.empty:
    # dynamic colors
    colors=itertools.cycle(['blue','green','red','orange','purple','darkred','cadetblue','pink'])
    cmap={s:next(colors) for s in subs}
    # center
    lat=fdf['latitude'].mean(); lon=fdf['longitude'].mean()
    m=folium.Map([lat,lon],11,control_scale=True)
    Fullscreen(position='topright', title='Full', title_cancel='Exit', force_separate_button=True).add_to(m)
    if show_heatmap: HeatMap([[r['latitude'],r['longitude']] for _,r in fdf.iterrows()], radius=12,blur=15).add_to(m)
    if show_markers:
        for _,r in fdf.iterrows(): folium.Marker([r['latitude'],r['longitude']], icon=folium.Icon(*icon_map.get(r['sub_category'],('map-marker','gray')), prefix='fa')).add_to(m)
    # termales
    for _,r in termales.iterrows(): folium.Marker([r['latitude'],r['longitude']], icon=folium.Icon(color='darkpurple',icon='water',prefix='fa')).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, width='100%',height=600)
    # table
    st.markdown('### Datos filtrados')
    cols=['name','municipio','sub_category','types','average_rating','user_ratings_total','latitude','longitude']
    table=fdf[cols].sort_values('average_rating',ascending=False)
    st.dataframe(table,use_container_width=True)
    st.download_button('Descargar CSV',table.to_csv(index=False),file_name='datos.csv',mime='text/csv')
else:
    st.info('Seleccione corredor, municipios e info_type para mostrar datos.')
