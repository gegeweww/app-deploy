import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from utils import get_table_cached

def run():
    st.title("📊 Dashboard Penjualan Optik")

    df = get_table_cached("pembayaran")
    df_transaksi = get_table_cached("transaksi_detail")

    if df.empty:
        st.warning("Data pembayaran belum tersedia.")
        return

    required_cols = ["tanggal_bayar", "nominal_pembayaran", "user_name"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom {col} tidak ditemukan di Supabase.")
            st.stop()

    # Bersihkan data pembayaran
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

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Bulan Ini", f"Rp {total_bulan_ini:,.0f}".replace(",", "."))
    col2.metric("📆 Tahun Ini", f"Rp {total_tahun_ini:,.0f}".replace(",", "."))
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

    y_max = df_chart["nominal_pembayaran"].max()
    tick_vals = np.linspace(0, y_max, 6)
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
        separators=".,"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # KATEGORI PENJUALAN
    # =========================
    st.subheader("📦 Kategori Penjualan", divider="rainbow")

    if df_transaksi.empty:
        st.warning("Data transaksi detail belum tersedia.")
    else:
        df_transaksi.columns = df_transaksi.columns.str.lower()

        # Parse tanggal
        df_transaksi["tanggal"] = pd.to_datetime(df_transaksi["tanggal"], errors="coerce")
        df_transaksi = df_transaksi.dropna(subset=["tanggal"])
        df_transaksi["tahun_t"] = df_transaksi["tanggal"].dt.year
        df_transaksi["bulan_t"] = df_transaksi["tanggal"].dt.month

        df_trx_bulan = df_transaksi[
            (df_transaksi["tahun_t"] == tahun_sekarang) &
            (df_transaksi["bulan_t"] == bulan_sekarang)
        ]

        # ==============================
        # FUNGSI KATEGORI FRAME
        # ==============================
        def kategorikan_frame(row):
            if row["status_frame"] == "Punya Sendiri":
                return "Punya Sendiri"
            harga = pd.to_numeric(row.get("harga_frame", 0), errors="coerce") or 0
            if harga < 300000:
                return "<Rp300.000"
            elif harga < 700000:
                return "Rp300.000 - Rp700.000"
            elif harga < 1500000:
                return "Rp700.000 - Rp1.500.000"
            else:
                return ">Rp1.500.000"

        df_transaksi["kategori_frame"] = df_transaksi.apply(kategorikan_frame, axis=1)
        df_trx_bulan["kategori_frame"] = df_trx_bulan.apply(kategorikan_frame, axis=1)

        # Hitung frame
        urutan_frame = [
            "<Rp300.000",
            "Rp300.000 - Rp700.000",
            "Rp700.000 - Rp1.500.000",
            ">Rp1.500.000",
            "Punya Sendiri"
        ]

        frame_total = df_transaksi["kategori_frame"].value_counts().rename("Total")
        frame_bulan = df_trx_bulan["kategori_frame"].value_counts().rename("Bulan Ini")

        df_frame_tabel = pd.DataFrame({
            "Bulan Ini": frame_bulan,
            "Total": frame_total
        }).fillna(0).astype(int)

        df_frame_tabel = df_frame_tabel.reindex(
            [k for k in urutan_frame if k in df_frame_tabel.index]
        )
        df_frame_tabel.index.name = "Kategori Frame"

        # Hitung status lensa
        status_total = df_transaksi["status_lensa"].value_counts().rename("Total")
        status_bulan = df_trx_bulan["status_lensa"].value_counts().rename("Bulan Ini")

        df_status_tabel = pd.DataFrame({
            "Bulan Ini": status_bulan,
            "Total": status_total
        }).fillna(0).astype(int)
        df_status_tabel.index.name = "Status Lensa"

    # Urutan fix sesuai tabel lensa
    urutan_tipe_jenis = [
        "Kryptok — HMC",
        "Progressive — Bluray",
        "Progressive — Flexi Cord BCL",
        "Progressive — Flexi Cord HMC",
        "Progressive — HMC",
        "Progressive — Photochromic",
        "Progressive — Photochromic Bluray",
        "Single Vision — Photochromic",
        "Single Vision — Photochromic Bluray",
    ]       
    df_transaksi["tipe_jenis"] = df_transaksi["tipe_lensa"] + " — " + df_transaksi["jenis_lensa"]
    df_trx_bulan["tipe_jenis"] = df_trx_bulan["tipe_lensa"] + " — " + df_trx_bulan["jenis_lensa"]

    tipejenis_total = df_transaksi["tipe_jenis"].value_counts().rename("Total")
    tipejenis_bulan = df_trx_bulan["tipe_jenis"].value_counts().rename("Bulan Ini")

    df_tipejenis_tabel = pd.DataFrame({
        "Bulan Ini": tipejenis_bulan,
        "Total": tipejenis_total
    }).fillna(0).astype(int)

    # Filter hanya yang ada di urutan, lalu reindex sesuai urutan
    df_tipejenis_tabel = df_tipejenis_tabel.reindex(
        [k for k in urutan_tipe_jenis if k in df_tipejenis_tabel.index]
    ).fillna(0).astype(int)
    df_tipejenis_tabel.index.name = "Tipe & Jenis Lensa"

    # ==============================
    # LAYOUT: Frame | Status Lensa
    # ==============================
    col_kiri, col_kanan = st.columns(2)

    with col_kiri:
        st.markdown("**🕶️ Penjualan Frame**")
        st.dataframe(df_frame_tabel, use_container_width=True)

    with col_kanan:
        st.markdown("**:goggles: Status Lensa**")
        st.dataframe(df_status_tabel, use_container_width=True)

    # ==============================
    # LAYOUT: Tipe & Jenis Lensa (full width)
    # ==============================
    st.markdown("**:goggles: Tipe & Jenis Lensa**")
    st.dataframe(df_tipejenis_tabel, use_container_width=True)

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
    st.dataframe(df_latest_display, use_container_width=True)