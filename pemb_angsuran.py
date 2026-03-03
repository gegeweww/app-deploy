import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    get_table_cached,
    insert_row_supabase,
    generate_id_pembayaran_supabase
)

@st.cache_data(ttl=30)
def load_data():
    df_pembayaran = get_table_cached("pembayaran")
    df_transaksi = get_table_cached("transaksi_detail")
    return df_pembayaran, df_transaksi


def run():
    st.title("💳 Pembayaran Angsuran / Pelunasan")

    if "pembayaran_berhasil" in st.session_state:
        info = st.session_state.pop("pembayaran_berhasil")
        st.success(
            f"✅ Pembayaran {info['id']} berhasil | "
            f"Status: {info['status']} | "
            f"Sisa: Rp {info['sisa']:,.0f}".replace(",", ".")
        )

    df_pembayaran, df_transaksi = load_data()

    if df_pembayaran.empty:
        st.success("Belum ada pembayaran.")
        return

    # ==============================
    # Ambil pembayaran terakhir per transaksi
    # ==============================
    df_status = (
        df_pembayaran
        .sort_values("pembayaran_ke")
        .groupby("id_transaksi", as_index=False)
        .last()
    )

    # ==============================
    # HITUNG ULANG STATUS DARI SISA
    # ==============================
    df_status["sisa"] = pd.to_numeric(df_status["sisa"], errors="coerce").fillna(0)
    df_status["is_lunas"] = df_status["sisa"] <= 0

    df_belum_lunas = df_status[~df_status["is_lunas"]]

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_belum_lunas.empty:
        st.success("Semua transaksi telah lunas!")
        return

    # ==============================
    # Loop transaksi belum lunas
    # ==============================
    for _, row in df_belum_lunas.iterrows():

        id_transaksi = row["id_transaksi"]
        nama = row["nama"]
        total = float(row["total_harga"])
        id_pelanggan = row["id_pelanggan"]
        no_hp = row["no_hp"]
        metode = row["metode"]
        sisa_sekarang = float(row["sisa"])

        # Ambil item
        df_item = df_transaksi[
            df_transaksi["id_transaksi"] == id_transaksi
        ]

        items = df_item[
            ["merk_frame", "merk_lensa", "jenis_lensa"]
        ].fillna("-")

        item_str = ", ".join(
            f"{r.merk_frame} | {r.merk_lensa} | {r.jenis_lensa}"
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
                    key=f"tgl_{id_transaksi}"
                )

                raw_input = st.text_input(
                    "💰 Nominal Bayar",
                    key=f"bayar_{id_transaksi}"
                )

                cleaned = re.sub(r"[^0-9]", "", raw_input)
                bayar = int(cleaned) if cleaned else 0

                st.markdown(
                    f"Nominal Diterima: Rp {bayar:,.0f}".replace(",", ".")
                )

            with col2:
                via = st.selectbox(
                    "Via Pembayaran",
                    [
                        "Cash",
                        "Qris EDC Mandiri",
                        "Qris EDC BCA",
                        "Qris Statis Mandiri",
                        "TF BCA",
                        "TF Mandiri"
                    ],
                    key=f"via_{id_transaksi}"
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
                    df_all["nominal_pembayaran"],
                    errors="coerce"
                ).sum()

                total_terbayar = total_sebelumnya + bayar

                # ==============================
                # LOGIC BARU YANG FIX
                # ==============================
                sisa_baru = total - total_terbayar

                if sisa_baru <= 0:
                    status_baru = "Lunas"
                    sisa_baru = 0
                else:
                    status_baru = "Belum Lunas"

                pembayaran_ke = df_all.shape[0] + 1

                id_pembayaran_baru = generate_id_pembayaran_supabase(
                    datetime.now(ZoneInfo("Asia/Jakarta"))
                )

                user = st.session_state.get("user", "Unknown")

                data_insert = {
                    "timestamp_log": datetime.now(ZoneInfo("Asia/Jakarta")),
                    "id_transaksi": id_transaksi,
                    "id_pembayaran": id_pembayaran_baru,
                    "id_pelanggan": id_pelanggan,
                    "tanggal": row["tanggal"],
                    "tanggal_bayar": tanggal_bayar,
                    "nama": nama,
                    "no_hp": no_hp,
                    "metode": metode,
                    "via": via,
                    "total_harga": total,
                    "nominal_pembayaran": bayar,
                    "sisa": sisa_baru,
                    "status": status_baru,
                    "pembayaran_ke": pembayaran_ke,
                    "user_name": user
                }

                insert_row_supabase("pembayaran", data_insert)

                st.session_state["pembayaran_berhasil"] = {
                    "id": id_transaksi,
                    "sisa": sisa_baru,
                    "status": status_baru
                }

                st.cache_data.clear()
                st.rerun()