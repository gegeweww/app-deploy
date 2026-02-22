import streamlit as st
import pandas as pd
from utils import get_table_cached

def run():
    st.title("📋 Log Aktivitas Frame")

    df = get_table_cached("log_frames")

    if df.empty:
        st.warning("Belum ada log frame.")
        return

    if "timestamp_log" in df.columns:
        df["timestamp_log"] = pd.to_datetime(df["timestamp_log"], errors="coerce")
        df = df.sort_values("timestamp_log", ascending=False)

    # Drop kolom id
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    df = df.reset_index(drop=True)
    df.index = df.index + 1
    
    df.columns = [
        col.replace('_', ' ').title()
        for col in df.columns
    ]

    st.dataframe(df, use_container_width=True)