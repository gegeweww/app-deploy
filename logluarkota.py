import streamlit as st
import pandas as pd
from utils import get_table_cached

@st.cache_data(ttl=60)
def load_data():
    df_detail = get_table_cached("pesanan_luar_kota_detail")
    df_pembayaran = get_table_cached("pembayaran_luar_kota")
    return df_detail, df_pembayaran


def run():
    st.title("📦 History Pesanan Luar Kota")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    df_detail, df_pembayaran = load_data()

    if df_detail.empty:
        st.info("Belum ada pesanan luar kota.")
        return

    # ==============================
    # FORMAT TANGGAL
    # ==============================
    df_detail["tanggal_ambil"] = pd.to_datetime(
        df_detail["tanggal_ambil"], errors="coerce"
    )

    df_detail = df_detail.dropna(subset=["tanggal_ambil"])

    df_detail["bulan"] = df_detail["tanggal_ambil"].dt.strftime("%B %Y")
    df_detail["tanggal"] = df_detail["tanggal_ambil"].dt.strftime("%d-%m-%Y")

    # ==============================
    # FORMAT UKURAN
    # ==============================
    def format_ukuran(sph, cyl, axis, add):
        return f"SPH: {sph}, CYL: {cyl}, Axis: {axis}, Add: {add}"

    df_detail["ukuran_r"] = df_detail.apply(
        lambda r: format_ukuran(
            r["sph_r"], r["cyl_r"], r["axis_r"], r["add_r"]
        ),
        axis=1
    )

    df_detail["ukuran_l"] = df_detail.apply(
        lambda r: format_ukuran(
            r["sph_l"], r["cyl_l"], r["axis_l"], r["add_l"]
        ),
        axis=1
    )

    # ==============================
    # HITUNG TOTAL PER HEADER
    # ==============================
    df_total = (
        df_detail
        .groupby("id_transaksi", as_index=False)["total_harga"]
        .sum()
    )

    df_detail = df_detail.merge(
        df_total,
        on="id_transaksi",
        suffixes=("", "_header")
    )

    # ==============================
    # AMBIL STATUS TERAKHIR PEMBAYARAN
    # ==============================
    if not df_pembayaran.empty:
        df_status = (
            df_pembayaran
            .sort_values("pembayaran_ke")
            .groupby("id_transaksi", as_index=False)
            .last()[["id_transaksi", "status"]]
        )

        df_detail = df_detail.merge(
            df_status,
            on="id_transaksi",
            how="left"
        )
    else:
        df_detail["status"] = "Belum Lunas"

    # ==============================
    # FILTER BULAN
    # ==============================
    bulan_opsi = ["-- Semua Bulan --"] + sorted(
        df_detail["bulan"].dropna().unique()
    )[::-1]

    bulan_terpilih = st.selectbox("📅 Pilih Bulan", bulan_opsi)

    if bulan_terpilih != "-- Semua Bulan --":
        df_detail = df_detail[
            df_detail["bulan"] == bulan_terpilih
        ]

    # ==============================
    # FILTER NAMA
    # ==============================
    keyword = st.text_input("🔍 Cari Nama").strip().lower()

    if keyword:
        df_detail = df_detail[
            df_detail["nama"].str.lower().str.contains(keyword)
        ]

    if df_detail.empty:
        st.info("Tidak ada data yang cocok.")
        return

    # ==============================
    # FORMAT RUPIAH
    # ==============================
    df_detail["total_harga_header"] = df_detail[
        "total_harga_header"
    ].apply(lambda x: f"Rp {int(x):,}".replace(",", "."))

    hasil = df_detail[[
        "tanggal",
        "id_transaksi",
        "nama",
        "jenis_lensa",
        "nama_lensa",
        "ukuran_r",
        "ukuran_l",
        "total_harga_header",
        "status",
        "user_name"
    ]].copy()

    # Replace underscore jadi spasi + kapital tiap kata
    hasil.columns = (
        hasil.columns
        .str.replace("_", " ")
        .str.title()
    )

    # Khusus kolom Total Harga Header → Total Harga
    hasil = hasil.rename(columns={
        "Total Harga Header": "Total Harga"
    })

    hasil = hasil.reset_index(drop=True)
    hasil.index = hasil.index + 1
    hasil.index.name = "No"

    st.dataframe(hasil, use_container_width=True)