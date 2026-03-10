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
        df["timestamp_log"] = pd.to_datetime(df["timestamp_log"], errors="coerce")
        df = df.sort_values("timestamp_log", ascending=False).reset_index(drop=True)

    # ==============================
    # FILTER SECTION
    # ==============================
    tipe_options = sorted(df["tipe"].dropna().unique().tolist())

    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        filter_tipe = st.selectbox(
            "Tipe",
            options=[""] + tipe_options,
            index=0,
            placeholder="Semua Tipe",
            key="loglensa_tipe"
        )

    # Merk options bergantung tipe
    if filter_tipe:
        df_merk_src = df[df["tipe"] == filter_tipe]
    else:
        df_merk_src = df

    merk_options = sorted(df_merk_src["merk"].dropna().unique().tolist())

    with col2:
        filter_merk = st.selectbox(
            "Merk",
            options=[""] + merk_options,
            index=0,
            placeholder="Semua Merk",
            key="loglensa_merk"
        )

    # Jenis options bergantung tipe + merk
    if filter_tipe and filter_merk:
        df_jenis_src = df[(df["tipe"] == filter_tipe) & (df["merk"] == filter_merk)]
    elif filter_tipe:
        df_jenis_src = df[df["tipe"] == filter_tipe]
    elif filter_merk:
        df_jenis_src = df[df["merk"] == filter_merk]
    else:
        df_jenis_src = df

    jenis_options = sorted(df_jenis_src["jenis"].dropna().unique().tolist())

    with col3:
        filter_jenis = st.selectbox(
            "Jenis",
            options=[""] + jenis_options,
            index=0,
            placeholder="Semua Jenis",
            key="loglensa_jenis"
        )

    status_options = sorted(df["status"].dropna().unique().tolist())

    with col4:
        filter_status = st.selectbox(
            "Status",
            options=[""] + status_options,
            index=0,
            placeholder="Semua Status",
            key="loglensa_status"
        )

    if st.button("🔄 Reset", key="loglensa_reset"):
        st.session_state.pop("loglensa_tipe", None)
        st.session_state.pop("loglensa_merk", None)
        st.session_state.pop("loglensa_jenis", None)
        st.session_state.pop("loglensa_status", None)
        st.rerun()

    # ==============================
    # APPLY FILTER
    # ==============================
    filtered_df = df.copy()

    if filter_tipe:
        filtered_df = filtered_df[filtered_df["tipe"] == filter_tipe]
    if filter_merk:
        filtered_df = filtered_df[filtered_df["merk"] == filter_merk]
    if filter_jenis:
        filtered_df = filtered_df[filtered_df["jenis"] == filter_jenis]
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

    st.dataframe(df_display, width='stretch')
