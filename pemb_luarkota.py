import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    get_table_cached,
    insert_row_supabase,
    generate_id_pemb_skw_supabase
)

@st.cache_data(ttl=30)
def load_data():
    df_pembayaran = get_table_cached("pembayaran_luar_kota")
    df_detail = get_table_cached("pesanan_luar_kota_detail")
    df_header = get_table_cached("pesanan_luar_kota")
    return df_pembayaran, df_detail, df_header


def run():
    st.title("💳 Pembayaran Angsuran Luar Kota")
    if "pembayaran_luar_berhasil" in st.session_state:
        info = st.session_state.pop("pembayaran_luar_berhasil")
        st.success(
            f"✅ Pembayaran {info['id']} berhasil | "
            f"Status: {info['status']} | "
            f"Sisa: Rp {info['sisa']:,.0f}".replace(",", ".")
        )

    df_pembayaran, df_detail, df_header = load_data()

    if df_pembayaran.empty:
        st.success("Belum ada pembayaran luar kota.")
        return

    # ==============================
    # METRICS
    # ==============================
    st.subheader("📊 Ringkasan")

    df_pmb = df_pembayaran.copy()
    df_pmb["tanggal_bayar"] = pd.to_datetime(df_pmb["tanggal_bayar"], errors="coerce")
    df_pmb["nominal_pembayaran"] = pd.to_numeric(df_pmb["nominal_pembayaran"], errors="coerce").fillna(0)
    df_pmb["sisa"] = pd.to_numeric(df_pmb["sisa"], errors="coerce").fillna(0)

    now = datetime.now()
    bulan_ini = now.month
    tahun_ini = now.year

    df_pmb["bulan"] = df_pmb["tanggal_bayar"].dt.month
    df_pmb["tahun"] = df_pmb["tanggal_bayar"].dt.year

    total_bulan_ini = df_pmb[
        (df_pmb["bulan"] == bulan_ini) & (df_pmb["tahun"] == tahun_ini)
    ]["nominal_pembayaran"].sum()

    total_tahun_ini = df_pmb[
        df_pmb["tahun"] == tahun_ini
    ]["nominal_pembayaran"].sum()

    # Sisa belum dibayar per orang (semua waktu)
    df_status_terakhir = (
        df_pembayaran
        .sort_values("pembayaran_ke")
        .groupby("id_transaksi", as_index=False)
        .last()
    )
    df_status_terakhir["sisa"] = pd.to_numeric(df_status_terakhir["sisa"], errors="coerce").fillna(0)
    df_belum = df_status_terakhir[df_status_terakhir["sisa"] > 0]

    sisa_nelly = df_belum[df_belum["nama"] == "Nelly"]["sisa"].sum()
    sisa_rahmat = df_belum[df_belum["nama"] == "Rahmat"]["sisa"].sum()

    st.markdown("**Pemasukan**")
    m1, m2 = st.columns(2)
    m1.metric("💰 Bulan Ini", f"Rp {total_bulan_ini:,.0f}".replace(",", "."))
    m2.metric("📆 Tahun Ini", f"Rp {total_tahun_ini:,.0f}".replace(",", "."))

    st.markdown("**Belum Dibayar**")
    m3, m4 = st.columns(2)
    m3.metric("⏳ Nelly", f"Rp {sisa_nelly:,.0f}".replace(",", "."))
    m4.metric("⏳ Rahmat", f"Rp {sisa_rahmat:,.0f}".replace(",", "."))

    st.divider()

    # ==============================
    # Ambil pembayaran terakhir
    # ==============================
    df_status = (
        df_pembayaran
        .sort_values("pembayaran_ke")
        .groupby("id_transaksi", as_index=False)
        .last()
    )

    df_status["sisa"] = pd.to_numeric(df_status["sisa"], errors="coerce").fillna(0)
    df_status["is_lunas"] = df_status["sisa"] <= 0

    df_belum_lunas = df_status[~df_status["is_lunas"]]

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_belum_lunas.empty:
        st.success("Semua pesanan luar kota telah lunas!")
        return

    # ==============================
    # LOOP TRANSAKSI BELUM LUNAS
    # ==============================
    for _, row in df_belum_lunas.iterrows():

        id_transaksi = row["id_transaksi"]
        nama = row["nama"]
        total = float(row["total_harga"])
        metode = row["metode"]
        sisa_sekarang = float(row["sisa"])

        df_item = df_detail[
            df_detail["id_transaksi"] == id_transaksi
        ]

        items = df_item[
            ["merk_lensa", "nama_lensa", "jenis_lensa"]
        ].fillna("-")

        item_str = ", ".join(
            f"{r.merk_lensa} | {r.nama_lensa} | {r.jenis_lensa}"
            for _, r in items.iterrows()
        )

        with st.expander(
            f"{id_transaksi} - {nama} "
            f"(Sisa: Rp {sisa_sekarang:,.0f}".replace(",", ".") + ")"
        ):

            st.markdown(f"**Item:** {item_str}")
            st.markdown(f"**Total:** Rp {total:,.0f}".replace(",", "."))
            st.markdown(f"**Sisa Saat Ini:** Rp {sisa_sekarang:,.0f}".replace(",", "."))

            col1, col2 = st.columns(2)

            with col1:
                tanggal_bayar = st.date_input(
                    "📅 Tanggal Bayar",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    key=f"tgl_luar_{id_transaksi}"
                )

                raw_input = st.text_input(
                    "💰 Nominal Bayar",
                    key=f"bayar_luar_{id_transaksi}"
                )

                cleaned = re.sub(r"[^0-9]", "", raw_input)
                bayar = int(cleaned) if cleaned else 0

                st.markdown(
                    f"Nominal Diterima: Rp {bayar:,.0f}".replace(",", ".")
                )

            with col2:
                via = st.selectbox(
                    "Via Pembayaran",
                    ["Cash", "TF BCA", "TF Mandiri"],
                    key=f"via_luar_{id_transaksi}"
                )

            # ==============================
            # UPDATE PEMBAYARAN
            # ==============================
            if st.button(f"🔄 Update {id_transaksi}"):

                if bayar <= 0:
                    st.warning("Nominal harus lebih dari 0")
                    st.stop()

                df_all = df_pembayaran[
                    df_pembayaran["id_transaksi"] == id_transaksi
                ]

                total_sebelumnya = pd.to_numeric(
                    df_all["total_harga"] - df_all["sisa"],
                    errors="coerce"
                ).sum()

                total_terbayar = total_sebelumnya + bayar

                sisa_baru = total - total_terbayar

                if sisa_baru <= 0:
                    status_baru = "Lunas"
                    sisa_baru = 0
                else:
                    status_baru = "Belum Lunas"

                pembayaran_ke = df_all.shape[0] + 1

                id_pembayaran_baru = generate_id_pemb_skw_supabase(
                    nama, row["tanggal_ambil"]
                )

                user = st.session_state.get("user", "Unknown")

                data_insert = {
                    "timestamp_log": datetime.now(ZoneInfo("Asia/Jakarta")),
                    "tanggal_ambil": row["tanggal_ambil"],
                    "tanggal_bayar": tanggal_bayar,
                    "id_transaksi": id_transaksi,
                    "id_pembayaran": id_pembayaran_baru,
                    "nama": nama,
                    "metode": metode,
                    "via": via,
                    "total_harga": total,
                    "nominal_pembayaran": bayar,
                    "sisa": sisa_baru,
                    "pembayaran_ke": pembayaran_ke,
                    "status": status_baru,
                    "user_name": user
                }

                insert_row_supabase("pembayaran_luar_kota", data_insert)

                st.session_state["pembayaran_luar_berhasil"] = {
                    "id": id_transaksi,
                    "sisa": sisa_baru,
                    "status": status_baru
                }

                st.cache_data.clear()
                st.rerun()
