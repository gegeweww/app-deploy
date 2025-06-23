import streamlit as st
from datetime import datetime
import pandas as pd
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES
from utils import get_gsheet_client

def run():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Silakan pilih user terlebih dahulu di halaman utama.")
        st.stop()

    user = st.session_state["user"]
    client = get_gsheet_client(JSON_PATH)

    # Akses sheet utama dan logframe
    sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["dframe"])
    log_sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["logframe"])

    # Ambil semua data dari sheet utama ke DataFrame
    def get_data_df():
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        df['Kode'] = df['Kode'].astype(str)
        return df

    # Fungsi untuk menambah atau mengedit stok
    def proses_stock(merk, kode, jumlah, mode):
        try:
            cell = sheet.find(kode)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if cell:
                current_stock = int(sheet.cell(cell.row, 5).value)
                if mode == 'Tambah Stock':
                    new_stock = current_stock + jumlah
                    sheet.update_cell(cell.row, 5, new_stock)
                    st.success(f"Stock {merk} (Kode: {kode}) berhasil DITAMBAH! Stock sekarang: {new_stock}")
                    log_sheet.append_row([now, merk, kode, jumlah, mode, user])
                elif mode == 'Edit Stock':
                    sheet.update_cell(cell.row, 5, jumlah)
                    st.success(f"Stock {merk} (Kode: {kode}) berhasil DIEDIT menjadi {jumlah}!")
                    log_sheet.append_row([now, merk, kode, jumlah, mode, user])
            else:
                st.error(f"Kode {kode} tidak ditemukan!")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

    # UI Streamlit
    st.title('➕ Input / Edit Stock Frame')
    st.write('Tambahkan atau ubah stock dari frame yang tersedia')

    df = get_data_df()

    mode = st.selectbox('Pilih Mode:', ['Tambah Stock', 'Edit Stock'])

    merk_list = sorted(df['Merk'].dropna().unique())
    selected_merk = st.selectbox('Pilih Merk Frame:', merk_list)

    filtered_df = df[df['Merk'] == selected_merk]
    kode_list = sorted(filtered_df['Kode'].unique())
    selected_kode = st.selectbox('Pilih Kode Frame:', kode_list)

    jumlah_input = st.number_input('Jumlah', min_value=0, step=1)

    if st.button('Proses'):
        if selected_merk and selected_kode and jumlah_input is not None:
            proses_stock(selected_merk, selected_kode, jumlah_input, mode)
        else:
            st.error('Harap isi semua kolom dengan benar!')
