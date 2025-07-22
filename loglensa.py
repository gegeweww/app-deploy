
from utils import get_dataframe
from constants import SHEET_KEY, SHEET_NAMES
import streamlit as st

def run():
    @st.cache_data(ttl=300)
    def show_data():
        return get_dataframe(SHEET_KEY, SHEET_NAMES["loglensa"])

    st.title("📋 Log Aktivitas Lensa")
    st.write("Menampilkan seluruh log aktivitas untuk produk Lensa.")

    df = show_data()
    st.dataframe(df)