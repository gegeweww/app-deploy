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
        df = df.sort_values("timestamp_log", ascending=False).reset_index(drop=True)

    # ==============================
    # FILTER SECTION
    # ==============================
    merk_options = sorted(df["merk"].dropna().unique().tolist())

    col1, col2, col3 = st.columns([3, 3, 2])

    with col1:
        filter_merk = st.selectbox(
            "Merk",
            options=[""] + merk_options,
            index=0,
            placeholder="Semua Merk",
            key="logframe_merk"
        )

    # Kode options bergantung pada merk yang dipilih
    if filter_merk:
        df_kode_src = df[df["merk"] == filter_merk]
    else:
        df_kode_src = df

    kode_options = sorted(df_kode_src["kode"].dropna().unique().tolist())

    with col2:
        filter_kode = st.selectbox(
            "Kode",
            options=[""] + kode_options,
            index=0,
            placeholder="Semua Kode",
            key="logframe_kode"
        )

    status_options = sorted(df["status"].dropna().unique().tolist())

    with col3:
        filter_status = st.selectbox(
            "Status",
            options=[""] + status_options,
            index=0,
            placeholder="Semua Status",
            key="logframe_status"
        )

    if st.button("🔄 Reset", key="logframe_reset"):
        st.session_state.pop("logframe_merk", None)
        st.session_state.pop("logframe_kode", None)
        st.session_state.pop("logframe_status", None)
        st.rerun()

    # ==============================
    # APPLY FILTER
    # ==============================
    filtered_df = df.copy()

    if filter_merk:
        filtered_df = filtered_df[filtered_df["merk"] == filter_merk]
    if filter_kode:
        filtered_df = filtered_df[filtered_df["kode"] == filter_kode]
    if filter_status:
        filtered_df = filtered_df[filtered_df["status"] == filter_status]

    st.caption(f"Menampilkan {len(filtered_df)} dari {len(df)} log")

    # ==============================
    # TAMPIL DATA
    # ==============================
    df_display = filtered_df.drop(columns=["id"], errors="ignore").reset_index(drop=True)
    df_display.index = df_display.index + 1
    df_display.index.name = "No"
    df_display.columns = [col.replace("_", " ").title() for col in df_display.columns]

    st.dataframe(df_display, use_container_width=True)
