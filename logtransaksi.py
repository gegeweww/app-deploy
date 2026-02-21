import streamlit as st
import pandas as pd
from utils import get_table_cached


def run():
    st.title("📜 Data Transaksi Optik Maroon")

    # ==============================
    # Ambil Data
    # ==============================
    df_detail = get_table_cached("transaksi_detail")
    df_pembayaran = get_table_cached("pembayaran")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_detail.empty:
        st.warning("Data transaksi belum tersedia.")
        return

    # Normalisasi kolom
    df_detail.columns = df_detail.columns.str.strip().str.lower().str.replace(' ', '_')
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(' ', '_')

    # ==============================
    # Ambil status terakhir pembayaran
    # ==============================
    if not df_pembayaran.empty and "pembayaran_ke" in df_pembayaran.columns:
        df_status = (
            df_pembayaran
            .sort_values(by='pembayaran_ke')
            .groupby('id_transaksi', as_index=False)
            .last()
        )[['id_transaksi', 'status']]
    else:
        df_status = pd.DataFrame(columns=['id_transaksi', 'status'])

    # Merge status ke detail
    df_ringkas = df_detail.merge(
        df_status,
        on='id_transaksi',
        how='left'
    )

    # ==============================
    # Pilih Kolom
    # ==============================
    selected_cols = [
        'tanggal',
        'id_transaksi',
        'nama',
        'merk_frame',
        'kode_frame',
        'jenis_lensa',
        'tipe_lensa',
        'harga_frame',
        'harga_lensa',
        'total_harga',
        'status',
        'user_name'
    ]

    df_ringkas = df_ringkas[
        [col for col in selected_cols if col in df_ringkas.columns]
    ]

    # ==============================
    # Format tanggal
    # ==============================
    df_ringkas['tanggal'] = pd.to_datetime(
        df_ringkas['tanggal'],
        errors='coerce'
    )

    df_ringkas = df_ringkas.dropna(subset=['tanggal'])

    df_ringkas['tahun'] = df_ringkas['tanggal'].dt.year
    df_ringkas['bulan_num'] = df_ringkas['tanggal'].dt.month
    df_ringkas['bulan_nama'] = df_ringkas['tanggal'].dt.strftime('%B')

    df_ringkas['tanggal'] = df_ringkas['tanggal'].dt.strftime('%d-%m-%Y')

    # ==============================
    # 🎛 FILTER SECTION
    # ==============================

    col1, col2, col3 = st.columns(3)

    # ---- FILTER TAHUN ----
    tahun_list = sorted(df_ringkas['tahun'].unique(), reverse=True)
    with col1:
        selected_tahun = st.selectbox("Pilih Tahun", tahun_list)

    df_filtered = df_ringkas[df_ringkas['tahun'] == selected_tahun]

    # ---- FILTER BULAN ----
    bulan_tersedia = (
        df_filtered[['bulan_num', 'bulan_nama']]
        .drop_duplicates()
        .sort_values('bulan_num')
    )

    bulan_options = ["Semua"] + bulan_tersedia['bulan_nama'].tolist()

    with col2:
        selected_bulan = st.selectbox("Pilih Bulan", bulan_options)

    if selected_bulan != "Semua":
        df_filtered = df_filtered[df_filtered['bulan_nama'] == selected_bulan]

    # ---- SEARCH NAMA ----
    with col3:
        search_nama = st.text_input("🔍 Cari Nama")

    if search_nama:
        df_filtered = df_filtered[
            df_filtered['nama'].str.contains(search_nama, case=False, na=False)
        ]
        
    # ==============================
    # Display
    # ==============================
    if not df_filtered.empty:
        df_display = df_filtered.drop(columns=['bulan'], errors='ignore')
        df_display = df_display.reset_index(drop=True)
        df_display = df_filtered.drop(
            columns=['tahun', 'bulan_num', 'bulan_nama'],
            errors='ignore'
        )
        df_display.index = df_display.index + 1
        df_display.index.name = "No"


        df_display.columns = [
            col.replace('_', ' ').title()
            for col in df_display.columns
        ]

        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Tidak ada data ditemukan.")
        
