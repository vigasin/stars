import sys
from datetime import datetime
import random
import time
import asyncio

import folium
import pandas as pd
import numpy as np
import requests
import streamlit as st
from folium.plugins import HeatMap

from streamlit_autorefresh import st_autorefresh

page_title = "Nx Real-Time / Live Activations Dashboard"
st.set_page_config(layout="wide", page_title=page_title)

st_autorefresh(interval=30 * 1000, key="dataframerefresh")

from streamlit_folium import st_folium


def generateBaseMap(loc, zoom=4, tiles='OpenStreetMap', crs='ESPG2263'):
    return folium.Map(  # location=loc,
        control_scale=True,
        zoom_start=zoom,
        tiles=tiles)


@st.experimental_memo
def get_data():
    df = pd.read_csv('http://stars.hdw.mx:8000/activations_after/')

    df['channels'] = df['channels'] / df['channels'].sum()
    map_values1 = df[['latitude', 'longitude', 'channels']]
    return map_values1.values.tolist()


def get_stats():
    r = requests.get('http://stars.hdw.mx:8000/stats/')
    return r.json()


def get_latest():
    df = pd.read_csv('http://stars.hdw.mx:8000/latest_activations/')
    df['Date'] = df['Date'].apply(format_ts)
    return df


def format_ts(iso_ts):
    return datetime.fromisoformat(iso_ts).strftime('%m/%d/%Y %H:%M:%S UTC')


if __name__ == '__main__':
    st.title(page_title)

    # data_load_state = st.text('Loading data...')
    data = get_data()
    # data_load_state.text('Loading data...done!')

    # gradient = {0.1: 'blue', 0.3: 'lime', 0.5: 'yellow', 0.7: 'orange', 1: 'red'}
    # hm =

    default_center = (37.16031654673677, 160.13671875000003)
    default_zoom = 2

    # creating a single-element container.
    placeholder = st.empty()

    with placeholder.container():
        # m = generateBaseMap([39, -98])
        latest_df = get_latest()

        m = folium.Map(control_scale=True,
                       location=default_center,
                       tiles='OpenStreetMap')

        hm = HeatMap(data, gradient={0.1: 'yellow', 0.5: 'red', 0.9: 'brown'},
                     min_opacity=0.4,
                     max_opacity=0.9,
                     radius=5,
                     blur=5,
                     use_local_extrema=False)
        m.add_child(hm)

        fg = folium.FeatureGroup(name="Markers")

        for index, row in latest_df.iterrows():
            ll = row['Location']
            if ll == 'None':
                continue

            channels = row['Channels']
            ll_split = ll.split(',')
            tooltip = folium.Tooltip(permanent=True, text=f'<b style="white-space: nowrap">{channels} channels</b>')
            marker = folium.Marker(
                (float(ll_split[0]), float(ll_split[1])), tooltip=tooltip)
            fg.add_child(marker)

        st_map = st_folium(m,
                           center=default_center,
                           zoom=default_zoom,
                           feature_group_to_add=fg,
                           width=1725,
                           returned_objects=[]
                           )

        # CSS to inject contained in a string
        hide_table_row_index = """
                    <style>
                    thead tr th:first-child {display:none}
                    tbody th {display:none}
                    </style>
                    """

        # Inject CSS with Markdown
        st.markdown(hide_table_row_index, unsafe_allow_html=True)

        st.subheader('Latest activations')

        st.table(latest_df.drop(['Location'], axis=1))

        # col1, col2, col3 = st.columns(3)
        # with col2:
        #     st.table(df)

        stats = get_stats()
        total_channels = stats['total_channels']
        latest_ts = format_ts(stats['latest_timestamp'])
        st.text(f'Totally activated {total_channels} channels by {latest_ts}')


