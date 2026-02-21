import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils import get_supabase

def run():
    st.title("📊 Dashboard Penjualan Optik")

    supabase = get_supabase()

    response = supabase.table("pembayaran").select("*").execute()

    if not response.data:
        st.warning("Data pembayaran tidak ditemukan.")
        st.stop()

    df = pd.DataFrame(response.data)

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

    col1.metric("💰 Bulan Ini", f"Rp {total_bulan_ini:,.0f}")
    col2.metric("📆 Tahun Ini", f"Rp {total_tahun_ini:,.0f}")
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

    fig = px.line(
        df_chart,
        x="bulan",
        y="nominal_pembayaran",
        markers=True,
        title=f"📈 Grafik Penjualan {tahun_pilih}"
    )

    fig.update_layout(
        yaxis=dict(
            tickprefix="Rp ",
            tickformat=",.0f",
            title="Pemasukan"
        )
    )

    fig.update_traces(
        hovertemplate="Bulan: %{x}<br>Nominal: Rp %{y:,.0f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # TRANSAKSI TERBARU
    # =========================
    st.subheader("🕒 Transaksi Terbaru")

    df_latest = df.sort_values("tanggal_bayar", ascending=False).head(5)
    df_latest_display = df_latest[[
        "tanggal_bayar",
        "id_transaksi",
        "nama",
        "nominal_pembayaran",
        "user_name"
    ]]

    st.dataframe(df_latest_display, use_container_width=True)