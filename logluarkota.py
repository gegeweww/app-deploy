import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_dataframe
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES

@st.cache_data(ttl=300)
def load_data():
    df_log = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pesanan_luar_kota'])
    df_pembayaran = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran_luar_kota'])
    return df_log, df_pembayaran

def run():
    st.title("📦 History Luar Kota")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Load
    try:
        df_log, df_pembayaran = load_data()
    except Exception as e:
        st.error(f"Gagal ambil data: {e}")
        return

    # Normalisasi kolom
    df_log.columns = df_log.columns.str.strip().str.lower().str.replace(" ", "_")
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(" ", "_")

    # Parse tanggal
    df_log['tanggal'] = pd.to_datetime(df_log['tanggal'], errors='coerce', dayfirst=True)
    df_log = df_log.dropna(subset=['tanggal'])
    df_log['bulan'] = df_log['tanggal'].dt.strftime('%B %Y')
    df_log['tanggal'] = df_log['tanggal'].dt.strftime('%d-%m-%Y')

    # Ukuran
    def format_ukuran(sph, cyl, axis, add):
        return f"SPH: {sph}, CYL: {cyl}, Axis: {axis}, Add: {add}"

    df_log['ukuran_r'] = df_log.apply(lambda r: format_ukuran(
        r.get('sph_r', ''), r.get('cyl_r', ''), r.get('axis_r', ''), r.get('add_r', '')
    ), axis=1)

    df_log['ukuran_l'] = df_log.apply(lambda r: format_ukuran(
        r.get('sph_l', ''), r.get('cyl_l', ''), r.get('axis_l', ''), r.get('add_l', '')
    ), axis=1)

    # Harga total
    df_log['total_harga'] = (
        pd.to_numeric(df_log.get('harga_lensa'), errors='coerce').fillna(0) +
        pd.to_numeric(df_log.get('ongkos_potong'), errors='coerce').fillna(0) +
        pd.to_numeric(df_log.get('ongkir'), errors='coerce').fillna(0)
    ).astype(int)

    # Gabung status terakhir
    df_status = (
        df_pembayaran.sort_values(by='ke')
        .groupby('id_transaksi', as_index=False)
        .last()[['id_transaksi', 'status']]
    )
    df_log = df_log.merge(df_status, on='id_transaksi', how='left')

    # Filter bulan
    bulan_opsi = ["-- Semua Bulan --"] + sorted(df_log['bulan'].dropna().unique())[::-1]
    bulan_terpilih = st.selectbox("📅 Pilih Bulan", bulan_opsi)

    if bulan_terpilih == "-- Semua Bulan --":
        df_bulan = df_log.copy()
    else:
        df_bulan = df_log[df_log['bulan'] == bulan_terpilih].copy()


    # Filter nama pelanggan
    keyword = st.text_input("🔍 Cari Nama (misal: Rahmat, Nelly)").strip().lower()
    if keyword:
        df_bulan = df_bulan[df_bulan['nama'].str.lower().str.contains(keyword)]

    if df_bulan.empty:
        st.info("Tidak ada data yang cocok.")
        return

    # Format akhir
    df_bulan['total_harga'] = df_bulan['total_harga'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))

    hasil = df_bulan[[
        'tanggal', 'id_transaksi', 'nama',
        'jenis_lensa', 'nama_lensa',
        'ukuran_r', 'ukuran_l',
        'total_harga', 'status', 'user'
    ]].reset_index(drop=True)

    st.markdown(f"### 📆 Data Bulan {bulan_terpilih}")
    st.dataframe(hasil, use_container_width=True)
