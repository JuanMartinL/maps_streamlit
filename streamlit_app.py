import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load your cleaned dataset
@st.cache_data
def load_data():
    return pd.read_csv("map_data.csv")

df = load_data()

# Sidebar filter
st.sidebar.title("Filter by Subcategory")
all_categories = sorted(df['sub_category'].unique())
selected_categories = st.sidebar.multiselect(
    "Select subcategories to display:",
    options=all_categories,
    default=all_categories
)

# Filtered data
filtered_df = df[df['sub_category'].isin(selected_categories)]

# Assign colors to each subcategory
import itertools
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
        popup=f"<b>{row['name']}</b><br>{row['municipio']}<br>{row['sub_category']}",
        icon=folium.Icon(color=color_map.get(row['sub_category'], "gray"))
    ).add_to(m)

# Display
st.title("Interactive Map of Points of Interest")
st.markdown("This map shows categorized touristic infrastructure. Filter by subcategory to explore.")
st_data = st_folium(m, width=800, height=600)