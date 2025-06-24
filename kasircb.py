import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import (
    get_dataframe, append_row,
    get_or_create_pelanggan_id, generate_id_transaksi, generate_id_pembayaran
)
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES
def run():
    @st.cache_data(ttl=300)
    def load_data():
        df_frame = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['dframe'])
        df_lensa = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['dlensa'])

        for df in (df_frame, df_lensa):
            for col in ['Harga Jual', 'Harga Modal']:
                df[col] = (
                    df[col].astype(str)
                    .replace(r'\s+', '0', regex=True)
                    .str.replace(r'[^\d]', '', regex=True)
                    .replace('', '0')
                    .astype(int)
                )
        return df_frame, df_lensa

    df_frame, df_lensa = load_data()

    st.title("🧾 Transaksi Kasir")
    today = datetime.today().strftime("%Y-%m-%d")
    tanggal_transaksi = st.date_input("📅 Tanggal Transaksi", value=date.today(), format="DD/MM/YYYY")
    tanggal_str = tanggal_transaksi.strftime("%Y-%m-%d")

    nama = st.text_input("Nama Konsumen")
    kontak = st.text_input("No HP")
    if not nama or not kontak:
        st.warning("Nama dan No HP harus diisi.")
        st.stop()

    nama = str(nama).strip().lower()
    kontak = str(kontak).strip()
    id_pelanggan = get_or_create_pelanggan_id(SHEET_KEY, JSON_PATH, SHEET_NAMES['pelanggan'], nama, kontak)

    if "daftar_item" not in st.session_state:
        st.session_state.daftar_item = []

    st.subheader("➕ Tambah Item")
    status_frame = st.selectbox("Status Frame", ["Stock", "Punya Sendiri"])
    if status_frame == "Stock":
        merk_options = [""] + sorted(df_frame['Merk'].dropna().unique())
        merk_frame = st.selectbox("Merk Frame", merk_options, format_func=lambda x: "-- Pilih Merk --" if x == "" else x)
        if merk_frame:
            kode_options = [""] + sorted(df_frame[df_frame['Merk'] == merk_frame]['Kode'].dropna().unique())
        else:
            kode_options = [""]            
        kode_frame = st.selectbox("Kode Frame", kode_options, format_func=lambda x: "-- Pilih Kode --" if x == "" else x)

        if not merk_frame or not kode_frame:
            st.warning("Merk dan Kode Frame harus dipilih.")
            st.stop()
    else:
        merk_frame, kode_frame = "", ""
        


    status_lensa = st.selectbox("Status Lensa", ["Stock", "Inti", "Pesan", "Overlens"])
    jenis_lensa = st.selectbox("Jenis Lensa", sorted(df_lensa['Jenis'].dropna().unique()))
    tipe_lensa = st.selectbox("Tipe Lensa", sorted(df_lensa[df_lensa['Jenis'] == jenis_lensa]['Tipe'].dropna().unique()))
    merk_lensa = st.selectbox("Merk Lensa", sorted(df_lensa[df_lensa['Jenis'] == jenis_lensa]['Merk'].dropna().unique()))

    st.markdown("**Ukuran Lensa**")
    colR, colL = st.columns(2)
    with colR:
        sph_r = st.selectbox("SPH R", sorted(df_lensa['SPH'].dropna().unique()))
        cyl_r = st.selectbox("CYL R", sorted(df_lensa['CYL'].dropna().unique()))
        axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
        add_r = st.selectbox("Add R", sorted(df_lensa['Add'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
    with colL:
        sph_l = st.selectbox("SPH L", sorted(df_lensa['SPH'].dropna().unique()))
        cyl_l = st.selectbox("CYL L", sorted(df_lensa['CYL'].dropna().unique()))
        axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
        add_l = st.selectbox("Add L", sorted(df_lensa['Add'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""

    st.markdown("**Pilih Diskon**")
    diskon_mode = st.radio("Jenis Diskon", ["Diskon Persen", "Diskon Lensa"])

    if diskon_mode == "Diskon Persen":
        diskon_persen = st.selectbox("Diskon (%)", [0, 5, 10, 15, 20])
        diskon_lensa = 0
    else:
        diskon_persen = 0
        diskon_lensa = st.number_input("Diskon Lensa (Rp)", min_value=0, step=500)

    if st.button("📝 Tambah ke Daftar"):
        if status_frame == "Stock":
            harga_frame = df_frame[(df_frame['Merk'] == merk_frame) & (df_frame['Kode'] == kode_frame)]['Harga Jual'].values[0]
        else:
            harga_frame = 0

        try:
            harga_lensa = df_lensa[(df_lensa['Jenis'] == jenis_lensa) & (df_lensa['Merk'] == merk_lensa)]['Harga Jual'].values[0]
            harga_lensa = 0 if status_lensa == "Overlens" else int(harga_lensa)
        except:
            harga_lensa = 0

        if diskon_mode == "Diskon Persen":
            diskon_nilai = (harga_frame + harga_lensa) * (diskon_persen / 100)
        else:
            diskon_nilai = diskon_lensa

        harga_setelah_diskon = harga_frame + harga_lensa - diskon_nilai

        st.session_state.daftar_item.append({
            "status_frame": status_frame,
            "merk_frame": merk_frame,
            "kode_frame": kode_frame,
            "status_lensa": status_lensa,
            "jenis_lensa": jenis_lensa,
            "tipe_lensa": tipe_lensa,
            "merk_lensa": merk_lensa,
            "sph_r": sph_r, "cyl_r": cyl_r, "axis_r": axis_r, "add_r": add_r,
            "sph_l": sph_l, "cyl_l": cyl_l, "axis_l": axis_l, "add_l": add_l,
            "harga_frame": harga_frame,
            "harga_lensa": harga_lensa,
            "diskon": diskon_nilai,
            "subtotal": harga_setelah_diskon
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item:
        st.subheader("📋 Daftar Item")
        df = pd.DataFrame(st.session_state.daftar_item)

        # Tombol hapus
        for i, item in enumerate(st.session_state.daftar_item):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** Frame {item['merk_frame']} | Lensa {item['merk_lensa']} ({item['jenis_lensa']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item.pop(i)
                    st.rerun()

        df = pd.DataFrame(st.session_state.daftar_item)
        total = df['subtotal'].sum()

        ribuan_digit = (total // 1000) % 10
        dasar = (total // 10000) * 10000
        harga_final = dasar + 5000 if ribuan_digit >= 5 else dasar
        pembulatan = harga_final - total

        st.markdown(f"### 💰 Total: Rp {total:,.0f}")
        st.markdown(f"### Pembulatan: Rp {pembulatan:,.0f}")
        st.markdown(f"### Total Harga: Rp {harga_final:,.0f}")

        metode = st.selectbox("Jenis Pembayaran", ["Angsuran", "Full"])
        via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"])
        nominal = st.number_input("Masukkan Nominal", min_value=0)
        sisa = nominal - harga_final
        status = "Lunas" if sisa >= 0 else "Belum Lunas"

        if sisa > 0:
            st.success(f"Kembalian: Rp {sisa:,.0f}")

        if st.button("💾 Simpan Pembayaran"):
            id_transaksi = generate_id_transaksi(SHEET_KEY, JSON_PATH, SHEET_NAMES['transaksi'], tanggal_transaksi)
            id_pembayaran = generate_id_pembayaran(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran'], tanggal_transaksi)
            user = st.session_state.get("user", "Unknown")

            for item in st.session_state.daftar_item:
                row = [today, tanggal_str, id_transaksi, id_pelanggan, nama,
                    item['status_frame'], item['merk_frame'], item['kode_frame'],
                    item['status_lensa'], item['jenis_lensa'], item['tipe_lensa'], item['merk_lensa'],
                    item['sph_r'], item['cyl_r'], item['axis_r'], item['add_r'],
                    item['sph_l'], item['cyl_l'], item['axis_l'], item['add_l'],
                    item['harga_frame'], item['harga_lensa'], int(item['diskon']), int(item['subtotal']), user]
                append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['transaksi'], [str(x) for x in row])

            df_pembayaran = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran'])
            pembayaran_ke = df_pembayaran[df_pembayaran['ID Transaksi'] == id_transaksi].shape[0] + 1

            pembayaran_data = [
                today, id_transaksi, id_pembayaran, id_pelanggan,
                tanggal_str, nama, kontak, metode, via, harga_final, nominal, sisa, status,
                pembayaran_ke, user
            ]
            append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['pembayaran'], [str(x) for x in pembayaran_data])

            st.session_state['ringkasan_tersimpan'] = {
                'id_transaksi': id_transaksi,
                'tanggal': today,
                'nama': nama.title(),
                'status': status,
                'sisa': sisa
            }
            del st.session_state.daftar_item
            st.rerun()

    if 'ringkasan_tersimpan' in st.session_state:
        data = st.session_state['ringkasan_tersimpan']
        with st.expander("✅ Pembayaran Berhasil", expanded=True):
            st.markdown(f"""
            **Tanggal Transaksi:** {data['tanggal']}  
            **ID Transaksi:** `{data['id_transaksi']}`  
            **Nama:** {data['nama']}  
            **Status:** {data['status']}  
            **Sisa/Kembalian:** Rp {data['sisa']:,.0f}
            """)
            if st.button("OK"):
                st.session_state.pop("ringkasan_tersimpan", None)
                st.rerun()
