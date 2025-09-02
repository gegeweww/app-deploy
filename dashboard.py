import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from constants import SHEET_KEY, SHEET_NAMES
from utils import get_dataframe  

def run():

    st.title("Dashboard Penjualan")
    df = get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran'])

    if df is None or df.empty:
        st.warning("Data pembayaran tidak ditemukan.")
        st.stop()

    if 'Tanggal' not in df.columns or 'Nominal Pembayaran' not in df.columns:
        st.error("Kolom 'Tanggal' atau 'Nominal Pembayaran' tidak ditemukan.")
        st.stop()

    df['Nominal Pembayaran'] = (df['Nominal Pembayaran'].astype(int))
    # --- Konversi tanggal ke datetime dan ambil tahun ---
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
    df['Tahun'] = df['Tanggal'].dt.year
    
    bulan_map = {
    'January': 'Januari',
    'February': 'Februari',
    'March': 'Maret',
    'April': 'April',
    'May': 'Mei',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'Agustus',
    'September': 'September',
    'October': 'Oktober',
    'November': 'November',
    'December': 'Desember'}
    df['Bulan'] = df['Tanggal'].dt.strftime('%B').map(bulan_map)
    
    bulan_order = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
    
    # --- Filter tahun (slicer) ---
    tahun_list = sorted(df['Tahun'].dropna().unique())
    tahun_pilih = st.selectbox("Pilih Tahun", tahun_list, index=len(tahun_list)-1)

    # --- Filter data ---
    df_tahun = df[df['Tahun'] == tahun_pilih].copy()
    
    c1, c2 = st.columns([3,1.4])
    with c1:
        # --- Agregasi per bulan ---
        df_chart = df_tahun.groupby('Bulan', as_index=False)['Nominal Pembayaran'].sum()
        df_chart['Bulan'] = pd.Categorical(df_chart['Bulan'], categories=bulan_order, ordered=True)
        df_chart = df_chart.sort_values('Bulan')

        # --- Plot ---
        fig = px.line(
            df_chart,
            x="Bulan",
            y="Nominal Pembayaran",
            markers=True,
            title=f"Grafik Penjualan {tahun_pilih}"
        )
        fig.update_layout(
            xaxis=dict(
                tickangle=-90
            ),
            yaxis=dict(
                tickprefix="Rp ",
                tickformat=",.0f",   # pakai koma ribuan
                title="Pemasukan"
            )
        )
        # Format tooltip
        fig.update_traces(
            hovertemplate="Bulan: %{x}<br>Nominal: Rp %{y:,.0f}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True, height=400)
    
    with c2:
        # --- Ambil bulan & tahun sekarang ---
        today = datetime.now()
        bulan_sekarang_eng = today.strftime("%B")
        bulan_sekarang = bulan_map[bulan_sekarang_eng]
        tahun_sekarang = today.year

        # --- Filter data bulan sekarang ---
        df_bulan_ini = df_tahun[df_tahun['Bulan'] == bulan_sekarang]

        if not df_bulan_ini.empty:
            total_bulan = df_bulan_ini['Nominal Pembayaran'].sum()
            total_bulan_fmt = f"Rp {total_bulan:,.0f}".replace(",", ".")
        else:
            total_bulan_fmt = "Rp 0"

        # Box info
        total_bulan = df_bulan_ini['Nominal Pembayaran'].sum() if not df_bulan_ini.empty else 0
        total_bulan_fmt = f"Rp {total_bulan:,.0f}".replace(",", ".")

        st.markdown(
            f"""
            <div style="
                display: flex; 
                flex-direction: column; 
                justify-content: center; 
                align-items: center; 
                height: 400px;
                border-radius: 15px; 
                background-color: transparent;
                border: 2px solid #404040;
                padding: 20px;
                ">
                <h4>Penjualan {bulan_sekarang} {tahun_pilih}</h4>
                <h4>{total_bulan_fmt}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )