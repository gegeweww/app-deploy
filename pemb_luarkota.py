import streamlit as st
import pandas as pd
import re
from datetime import datetime
from utils import get_dataframe, append_row, generate_id_pembayaran, generate_id_pemb_skw
from constants import SHEET_KEY, SHEET_NAMES

@st.cache_data(ttl=300)
def load_data():
    df_pembayaran = get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'])
    df_pesanan = get_dataframe(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'])
    return df_pembayaran, df_pesanan

def run():
    st.title("💳 Pembayaran Angsuran Luar Kota")

    if 'pembayaran_luar_berhasil' in st.session_state:
        info = st.session_state.pop('pembayaran_luar_berhasil')
        label = "Sisa" if info['sisa'] >= 0 else "💰 Kembalian"
        nilai = abs(info['sisa'])
        st.success(f"✅ Pembayaran untuk {info['id']} berhasil. Status: {info['status']} | {label}: Rp {nilai:,.0f}".replace(",", "."))

    df_pembayaran, df_pesanan = load_data()

    # Normalisasi
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(" ", "_")
    df_pesanan.columns = df_pesanan.columns.str.strip().str.lower().str.replace(" ", "_")

    # Format tanggal ambil
    df_pembayaran['tanggal_ambil'] = pd.to_datetime(df_pembayaran['tanggal_ambil'], errors='coerce')
    df_pembayaran = df_pembayaran.dropna(subset=['tanggal_ambil'])

    df_pembayaran['nominal'] = pd.to_numeric(df_pembayaran['nominal'], errors='coerce').fillna(0)
    df_pembayaran['total_harga'] = pd.to_numeric(df_pembayaran['total_harga'], errors='coerce').fillna(0)

    # Hitung total bayar per transaksi
    total_bayar = df_pembayaran.groupby('id_transaksi')['nominal'].sum().reset_index()
    total_bayar.columns = ['id_transaksi', 'total_bayar']

    # Ambil data terakhir per transaksi (untuk ambil nama, metode, dll)
    last_rows = df_pembayaran.sort_values(by=['ke']).groupby('id_transaksi', as_index=False).last()
    df_summary = last_rows.merge(total_bayar, on='id_transaksi')

    df_summary['sisa'] = df_summary['total_bayar'] - df_summary['total_harga']
    df_summary['status'] = df_summary['sisa'].apply(lambda x: "Lunas" if x >= 0 else "Belum Lunas")
    df_summary['tanggal_ambil'] = df_summary['tanggal_ambil'].dt.strftime("%d-%m-%Y")

    df_belum_lunas = df_summary[df_summary['status'] == 'Belum Lunas']

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_belum_lunas.empty:
        st.success("Semua pesanan luar kota telah lunas!")
        return

    for idx, row in df_belum_lunas.iterrows():
        id_transaksi = row['id_transaksi']
        nama = row['nama']
        sisa = float(row['sisa'])
        total = float(row['total_harga'])
        tanggal = row['tanggal_ambil']

        items = df_pesanan[df_pesanan['id_transaksi'] == id_transaksi]
        item_str = ", ".join(
            [f"{r['merk_lensa']} | {r['nama_lensa']} | {r['jenis_lensa']}" for _, r in items.iterrows()]
        )

        with st.expander(f"{id_transaksi} - {nama} (Sisa: Rp {sisa:,.0f})".replace(",", ".")):
            st.markdown(f"**Tanggal Ambil:** {tanggal}")
            st.markdown(f"**Nama:** {nama}")
            st.markdown(f"**Item:** {item_str}")
            st.markdown(f"**Total Harga:** Rp {total:,.0f}".replace(",", "."))
            st.markdown(f"**Sisa Saat Ini:** Rp {sisa:,.0f}".replace(",", "."))

            col1, col2 = st.columns(2)
            with col1:
                raw_input = st.text_input(f"💰 Nominal Bayar", value="", key=f"luar_{id_transaksi}")
                cleaned_input = re.sub(r"[^0-9]", "", raw_input)
                bayar = int(cleaned_input) if cleaned_input else 0
                st.markdown(f"Nominal Diterima: Rp {bayar:,.0f}".replace(",", "."))
            with col2:
                via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"], key=f"via_{id_transaksi}")

            if st.button(f"🔄 Update Pembayaran {id_transaksi}", key=f"submit_{id_transaksi}"):
                if bayar <= 0:
                    st.warning("Nominal harus lebih dari 0")
                    st.stop()

                df_all = df_pembayaran[df_pembayaran['id_transaksi'] == id_transaksi]
                total_sebelumnya = df_all['nominal'].sum()
                total_terbayar = total_sebelumnya + bayar
                sisa_baru = round(total_terbayar - total, 2)
                status_baru = "Lunas" if sisa_baru >= 0 else "Belum Lunas"

                tanggal_bayar = datetime.today().strftime("%d-%m-%Y")
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                ke = df_all.shape[0] + 1
                user = st.session_state.get("user", "Unknown")

                id_pembayaran_baru = generate_id_pemb_skw(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'], nama, tanggal)

                new_row = [
                    timestamp, tanggal, id_transaksi, id_pembayaran_baru,
                    nama, row['metode'], via, int(total), int(bayar),
                    int(sisa_baru), ke, tanggal_bayar, status_baru, user
                ]
                append_row(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'], [str(x) for x in new_row])

                st.session_state['pembayaran_luar_berhasil'] = {
                    'id': id_transaksi,
                    'sisa': sisa_baru,
                    'status': status_baru
                }

                st.cache_data.clear()
                st.rerun()
