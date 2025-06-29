import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_dataframe
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES

@st.cache_data(ttl=300)
def load_data():
    df_transaksi = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['transaksi'])
    df_pembayaran = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran'])
    return df_transaksi, df_pembayaran

def run():
    st.title("📜 Data Transaksi Optik Maroon")

    df_transaksi, df_pembayaran = load_data()
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


    # Normalisasi kolom
    df_transaksi.columns = df_transaksi.columns.str.strip().str.lower().str.replace(' ', '_')
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(' ', '_')

    # Ambil pembayaran terakhir untuk setiap transaksi
    df_status = (
        df_pembayaran
        .sort_values(by='ke')
        .groupby('id_transaksi', as_index=False)
        .last()
    )[['id_transaksi', 'status']]

    # Gabungkan data transaksi dengan status terakhir
    df_ringkas = (
        df_transaksi
        .merge(df_status, on='id_transaksi', how='left')
    )

    if 'nama' not in df_ringkas.columns:
        df_ringkas['nama'] = df_ringkas.get('nama', '')

    if 'user' not in df_ringkas.columns:
        df_ringkas['user'] = df_transaksi.get('user', '-')

    selected_cols = ['tanggal', 
                     'id_transaksi', 
                     'nama', 
                     'merk_frame', 
                     'jenis_lensa', 
                     'total_harga', 
                     'status', 
                     'user']
    df_ringkas = df_ringkas[[col for col in selected_cols if col in df_ringkas.columns]]

    df_ringkas['tanggal'] = pd.to_datetime(df_ringkas['tanggal'], errors='coerce')
    df_ringkas = df_ringkas.dropna(subset=['tanggal'])
    df_ringkas['bulan'] = df_ringkas['tanggal'].dt.strftime('%B %Y')

    # Filter berdasarkan bulan dan nama
    bulan_tersedia = df_ringkas['bulan'].dropna().unique()

    bulan_options = ["Semua"] + sorted(bulan_tersedia, reverse=True)
    selected_bulan = st.selectbox("Pilih Bulan", bulan_options)
 
    if selected_bulan != "Semua":
        df_filtered = df_ringkas[df_ringkas['bulan'] == selected_bulan]
    else:
        df_filtered = df_ringkas.copy()
                
    search_nama = st.text_input("🔍 Cari Nama Pelanggan")
    if search_nama:
        df_filtered = df_filtered[df_filtered['nama'].str.contains(search_nama, case=False, na=False)]

    st.dataframe(df_filtered.drop(columns=['bulan'], errors='ignore').reset_index(drop=True), use_container_width=True)

