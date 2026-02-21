import streamlit as st
import pandas as pd
from utils import get_table_cached

def run():
    st.title("📋 Log Aktivitas Lensa")
    
    df = get_table_cached("log_lensa")
    
    if df.empty:
        st.warning("Belum ada data.")
        return
    
    if "timestamp_log" in df.columns:
        df["timestamp_log"] = pd.to_datetime(df["timestamp_log"])
        df = df.sort_values("timestamp_log", ascending=False)
        
    # Drop kolom id
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    
    st.dataframe(df, use_container_width=True)