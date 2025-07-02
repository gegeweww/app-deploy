import streamlit as st
import pandas as pd
import re
from datetime import datetime
from utils import get_dataframe, append_row, generate_id_pembayaran
from constants import SHEET_KEY, SHEET_NAMES

@st.cache_data(ttl=300)
def load_data():
    df_pembayaran = get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran'])
    df_transaksi = get_dataframe(SHEET_KEY, SHEET_NAMES['transaksi'])
    return df_pembayaran, df_transaksi

def run():
    st.title("💳 Pembayaran Angsuran / Pelunasan")

    # Tampilkan popup jika pembayaran sebelumnya berhasil
    if 'pembayaran_berhasil' in st.session_state:
        info = st.session_state.pop('pembayaran_berhasil')
        if info['sisa'] >= 0:
            label = "Sisa"
            nilai = info['sisa']
        else:
            label = "💰 Kembalian"
            nilai = abs(info['sisa'])
        st.success(f"✅ Pembayaran untuk {info['id']} berhasil disimpan. Status sekarang: {info['status']} | {label}: Rp {nilai:,.0f}".replace(",", "."))

    df_pembayaran, df_transaksi = load_data()

    # normalisasikan kolom
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(' ', '_')
    df_transaksi.columns = df_transaksi.columns.str.strip().str.lower().str.replace(' ', '_')

    # Filter hanya yang belum lunas
    df_belum_lunas = (
        df_pembayaran
        .sort_values(by='ke')
        .groupby('id_transaksi', as_index=False)
        .last()
    )
    df_belum_lunas = df_belum_lunas[df_belum_lunas['status'].str.lower() == 'belum lunas']

    # debug data
    st.write("⬇️ Data Belum Lunas:", df_belum_lunas[['id_transaksi', 'nama', 'status']])
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_belum_lunas.empty:
        st.success("Semua transaksi telah lunas!")
        return

    for idx, row in df_belum_lunas.iterrows():
        id_transaksi = row['id_transaksi']
        nama = row['nama_pelanggan'] if 'nama_pelanggan' in row else row['nama']
        sisa = float(row['sisa'])
        try:
            total = float(row['total_harga'])
        except:
            total = float(row['nominal_pembayaran']) + abs(sisa)
        tanggal = str(row['tanggal']).strip()

        if "\n" in tanggal or "Name:" in tanggal or "tanggal" in tanggal:
            tanggal = datetime.today().strftime("%Y-%m-%d")

        df_item = df_transaksi[df_transaksi['id_transaksi'] == id_transaksi]
        items = df_item[['merk_frame', 'merk_lensa', 'jenis_lensa']].fillna('-').astype(str)
        item_list = [f"{r['merk_frame']} | {r['merk_lensa']} | {r['jenis_lensa']}" for _, r in items.iterrows()]
        item_str = ", ".join(item_list)

        with st.expander(f"{id_transaksi} - {nama} (Sisa: Rp {sisa:,.0f}".replace(",", ".") + ")"):
            st.markdown(f"**Tanggal Transaksi:** {tanggal}")
            st.markdown(f"**Nama:** {nama}")
            st.markdown(f"**Item:** {item_str}")
            st.markdown(f"**Total Harga:** Rp {total:,.0f}".replace(",", "."))
            st.markdown(f"**Sisa Saat Ini:** Rp {sisa:,.0f}".replace(",", "."))

            col1, col2 = st.columns(2)
            with col1:
                raw_input = st.text_input(f"💰 Nominal Bayar untuk {id_transaksi}", value="", key=f"bayar_{id_transaksi}")
                cleaned_input = re.sub(r"[^0-9]", "", raw_input)
                bayar = int(cleaned_input) if cleaned_input else 0
                st.markdown(f"Nominal Diterima: Rp {bayar:,.0f}".replace(",", "."))
            with col2:
                via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"], key=f"via_{id_transaksi}")

            if st.button(f"🔄 Update Pembayaran {id_transaksi}"):
                if bayar <= 0:
                    st.warning("Nominal harus lebih dari 0")
                    st.stop()

                df_all = df_pembayaran[df_pembayaran['id_transaksi'] == id_transaksi]
                total_sebelumnya = pd.to_numeric(df_all['nominal_pembayaran'], errors='coerce').sum()
                total_terbayar = total_sebelumnya + bayar
                sisa_baru = round(total_terbayar - total, 2)
                status_baru = "Lunas" if sisa_baru >= 0 else "Belum Lunas"

                tanggal_hari_ini = datetime.today().strftime("%Y-%m-%d")
                id_pembayaran_baru = generate_id_pembayaran(SHEET_KEY, SHEET_NAMES['pembayaran'], datetime.today())
                user = st.session_state.get("user", "Unknown")

                pembayaran_ke = df_all.shape[0] + 1

                new_row = [
                    tanggal_hari_ini, id_transaksi, id_pembayaran_baru, row['id_pelanggan'], tanggal,
                    nama, row['no_hp'], row['metode'], via,
                    str(int(total)), str(int(bayar)), str(int(sisa_baru)), status_baru,
                    str(pembayaran_ke), user
                ]
                append_row(SHEET_KEY, SHEET_NAMES['pembayaran'], new_row)


                st.session_state['pembayaran_berhasil'] = {
                    'id': id_transaksi,
                    'sisa': sisa_baru,
                    'status': status_baru
                }
                st.cache_data.clear()
                st.rerun()
