import streamlit as st
import pandas as pd
import re
from datetime import datetime
from utils import get_dataframe, append_row, generate_id_pembayaran
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES

@st.cache_data(ttl=300)
def load_data():
    df_pembayaran = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran_luar_kota'])
    df_pesanan = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pesanan_luar_kota'])
    return df_pembayaran, df_pesanan

def run():
    st.title("💳 Pembayaran Angsuran Luar Kota")

    if 'pembayaran_luar_berhasil' in st.session_state:
        info = st.session_state.pop('pembayaran_luar_berhasil')
        label = "Sisa" if info['sisa'] >= 0 else "💰 Kembalian"
        nilai = abs(info['sisa'])
        st.success(f"✅ Pembayaran untuk {info['id']} berhasil. Status: {info['status']} | {label}: Rp {nilai:,.0f}".replace(",", "."))

    df_pembayaran, df_pesanan = load_data()
    
    # 1. Normalisasi kolom
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(" ", "_")
    df_pesanan.columns = df_pesanan.columns.str.strip().str.lower().str.replace(" ", "_")

    # 2. Konversi ke datetime aman
    df_pembayaran['tanggal_ambil'] = pd.to_datetime(df_pembayaran['tanggal_ambil'], errors='coerce')

    # 3. Hapus baris dengan tanggal invalid (NaT)
    df_pembayaran = df_pembayaran.dropna(subset=['tanggal_ambil'])

    # 4. Pastikan sort dan group aman
    df_latest = (
        df_pembayaran.sort_values(by='tanggal_ambil')
        .groupby('id_transaksi', as_index=False)
        .last()
    )


    df_belum_lunas = df_latest[df_latest['status'].str.lower() == 'belum lunas']

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
        total = float(row.get('total_harga', 0))
        tanggal = str(row['tanggal_ambil']).strip()
        if any(x in tanggal.lower() for x in ['\n', 'name:', 'tanggal']):
            tanggal = datetime.today().strftime("%d-%m-%Y")

        items = df_pesanan[df_pesanan['id_transaksi'] == id_transaksi]
        item_str = ", ".join(
            [f"{r['merk_lensa']} | {r['nama_lensa']} | {r['jenis_lensa']}" for _, r in items.iterrows()]
        )

        with st.expander(f"{id_transaksi} - {nama} (Sisa: Rp {sisa:,.0f})".replace(",", ".")):
            st.markdown(f"**Tanggal:** {tanggal}")
            st.markdown(f"**Nama:** {nama}")
            st.markdown(f"**Item:** {item_str}")
            st.markdown(f"**Total Harga:** Rp {total:,.0f}".replace(",", "."))
            st.markdown(f"**Sisa Saat Ini:** Rp {sisa:,.0f}".replace(",", "."))

            raw_input = st.text_input(f"💰 Nominal Bayar untuk {id_transaksi}", value="", key=f"luar_{id_transaksi}")
            cleaned_input = re.sub(r"[^0-9]", "", raw_input)
            bayar = int(cleaned_input) if cleaned_input else 0

            st.markdown(f"Nominal Diterima: Rp {bayar:,.0f}".replace(",", "."))

            if st.button(f"🔄 Update Pembayaran {id_transaksi}"):
                if bayar <= 0:
                    st.warning("Nominal harus lebih dari 0")
                    st.stop()

                df_all = df_pembayaran[df_pembayaran['id_transaksi'] == id_transaksi]
                total_sebelumnya = pd.to_numeric(df_all['nominal'], errors='coerce').sum()
                total_terbayar = total_sebelumnya + bayar
                sisa_baru = round(total_terbayar - total, 2)
                status_baru = "Lunas" if sisa_baru >= 0 else "Belum Lunas"

                tanggal_hari_ini = datetime.today().strftime("%Y-%m-%d")
                id_pembayaran_baru = generate_id_pembayaran(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran_luar_kota'], datetime.today())
                user = st.session_state.get("user", "Unknown")
                ke = df_all.shape[0] + 1

                new_row = [
                    tanggal_hari_ini, id_transaksi, id_pembayaran_baru,
                    nama, tanggal, row['metode'], row['via'], total, bayar,
                    sisa_baru, status_baru, ke, user
                ]
                append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran_luar_kota'], [str(x) for x in new_row])

                st.session_state['pembayaran_luar_berhasil'] = {
                    'id': id_transaksi,
                    'sisa': sisa_baru,
                    'status': status_baru
                }
                st.cache_data.clear()
                st.rerun()
