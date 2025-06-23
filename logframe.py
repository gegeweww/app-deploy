
from utils import get_dataframe
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES
import streamlit as st

def run():
    @st.cache_data(ttl=300)
    def show_data():
        return get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES["logframe"])
    
    st.title("📋 Log Aktivitas Frame")
    st.write("Menampilkan seluruh log aktivitas untuk produk Frame.")

    df = show_data()
    st.dataframe(df)