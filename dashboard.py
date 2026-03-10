import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from utils import get_table_cached

def run():
    st.title("📊 Dashboard Penjualan Optik")

    df = get_table_cached("pembayaran")

    if df.empty:
        st.warning("Data pembayaran belum tersedia.")
        return

    required_cols = ["tanggal_bayar", "nominal_pembayaran", "user_name"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom {col} tidak ditemukan di Supabase.")
            st.stop()

    # Bersihkan data
    df["nominal_pembayaran"] = pd.to_numeric(
        df["nominal_pembayaran"], errors="coerce"
    ).fillna(0)

    df["tanggal_bayar"] = pd.to_datetime(df["tanggal_bayar"], errors="coerce")
    df = df.dropna(subset=["tanggal_bayar"])

    df["tahun"] = df["tanggal_bayar"].dt.year
    df["bulan"] = df["tanggal_bayar"].dt.month

    now = datetime.now()
    bulan_sekarang = now.month
    tahun_sekarang = now.year

    # =========================
    # KPI SECTION
    # =========================
    df_bulan_ini = df[
        (df["tahun"] == tahun_sekarang) &
        (df["bulan"] == bulan_sekarang)
    ]

    total_bulan_ini = df_bulan_ini["nominal_pembayaran"].sum()
    total_tahun_ini = df[df["tahun"] == tahun_sekarang]["nominal_pembayaran"].sum()
    total_transaksi = len(df_bulan_ini)

    col1, col2, col3, = st.columns(3)

    col1.metric("💰 Bulan Ini", f"Rp {total_bulan_ini:,.0f}".replace(",","."))
    col2.metric("📆 Tahun Ini", f"Rp {total_tahun_ini:,.0f}".replace(",","."))
    col3.metric("🧾 Transaksi Bulan Ini", total_transaksi)

    st.divider()

    # =========================
    # GRAFIK BULANAN
    # =========================
    tahun_list = sorted(df["tahun"].unique())
    tahun_pilih = st.selectbox("Pilih Tahun", tahun_list, index=len(tahun_list)-1)

    df_tahun = df[df["tahun"] == tahun_pilih]

    df_chart = (
        df_tahun
        .groupby("bulan", as_index=False)["nominal_pembayaran"]
        .sum()
        .sort_values("bulan")
    )
    df_chart["nominal_format"] = df_chart["nominal_pembayaran"] \
        .apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        
    fig = px.line(
        df_chart,
        x="bulan",
        y="nominal_pembayaran",
        markers=True,
        title=f"📈 Grafik Penjualan {tahun_pilih}"
    )
    
    fig.update_yaxes(
        tickformat=",.0f",
        separatethousands=True
    )

    fig.update_traces(
        hovertemplate="Bulan: %{x}<br>Nominal: %{customdata}<extra></extra>",
        customdata=df_chart["nominal_format"]
    )
    # Tentukan tick values otomatis
    y_max = df_chart["nominal_pembayaran"].max()
    tick_vals = np.linspace(0, y_max, 6)

    # Format ke rupiah Indonesia
    tick_text = [
        f"Rp {int(val):,}".replace(",", ".")
        for val in tick_vals
    ]

    fig.update_layout(
        yaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            title="Pemasukan"
        ),
        separators = ".,"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # TRANSAKSI TERBARU
    # =========================
    st.subheader("🕒 Transaksi Terbaru", divider="rainbow")

    df_latest = df.sort_values("tanggal_bayar", ascending=False).head(5)
    df_latest_display = df_latest[[
        "tanggal_bayar",
        "id_transaksi",
        "nama",
        "total_harga",
        "status",
        "user_name"
    ]]
    
    df_latest_display = df_latest_display.copy()
    df_latest_display["total_harga"] = df_latest_display["total_harga"] \
        .apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        
    df_latest_display.columns = [
        col.replace('_', ' ').title()
        for col in df_latest_display.columns
    ]
    df_latest_display = df_latest_display.reset_index(drop=True)
    df_latest_display.index = df_latest_display.index + 1
    df_latest_display.index.name = "No"
    st.dataframe(df_latest_display, width='stretch')