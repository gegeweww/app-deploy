import streamlit as st
import pandas as pd
from utils import get_dataframe
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES

def run():
    st.title("📖 History Pesanan Luar Kota")

    try:
        df = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pesanan_luar_kota'])
        df.columns = df.columns.str.strip()

        if df.empty:
            st.info("Belum ada data pesanan luar kota.")
            return

        # Filter berdasarkan tanggal atau nama
        with st.expander("🔍 Filter Data"):
            kolom_filter = st.selectbox("Filter berdasarkan", ["Tanggal Ambil", "Nama"])
            if kolom_filter == "Tanggal Ambil":
                tanggal_opsi = sorted(df['Tanggal Ambil'].unique(), reverse=True)
                tanggal_pilih = st.selectbox("Pilih Tanggal Ambil", tanggal_opsi)
                df = df[df['Tanggal Ambil'] == tanggal_pilih]
            else:
                nama_opsi = sorted(df['Nama'].unique())
                nama_pilih = st.selectbox("Pilih Nama", nama_opsi)
                df = df[df['Nama'] == nama_pilih]

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
