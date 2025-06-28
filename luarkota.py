import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import (
    get_dataframe, append_row,
    cari_harga_lensa_luar, cari_harga_lensa_stock
)
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES

def run():
    @st.cache_data(ttl=300)
    def load_data():
        df_frame = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['dframe'])
        df_lensa_stock = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['dlensa'])
        df_lensa_luar = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES['lensa_luar_stock'])

        for df in (df_frame, df_lensa_stock):
            for col in ['Harga Jual', 'Harga Modal']:
                df[col] = (
                    df[col].astype(str)
                    .replace(r'\s+', '0', regex=True)
                    .str.replace(r'[^\d]', '', regex=True)
                    .replace('', '0')
                    .astype(int)
                )
        df_lensa_luar.columns = df_lensa_luar.columns.str.lower().str.strip().str.replace(" ", "_")
        return df_frame, df_lensa_stock, df_lensa_luar

    df_frame, df_lensa_stock, df_lensa_luar = load_data()

    st.title("📦 Pesanan Luar Kota")
    today = datetime.today().strftime("%Y-%m-%d")
    colL, colR = st.columns(2)
    with colL:
        tanggal_ambil = st.date_input("📅 Tanggal Ambil", value=date.today(), format="DD/MM/YYYY")
        tanggal_ambil = tanggal_ambil.strftime("%Y-%m-%d")
    with colR:
        nama = st.selectbox("Nama Konsumen", ["Rahmat", "Nelly"])

    if "daftar_item_luar" not in st.session_state:
        st.session_state.daftar_item_luar = []

    st.subheader("➕ Tambah Item")

    status_lensa = st.selectbox("Status Lensa", ["Stock", "Inti", "Pesan", "Overlens"])
    df_lensa = df_lensa_stock.copy() if status_lensa == "Stock" else df_lensa_luar[df_lensa_luar['status'].str.lower() == status_lensa.lower()].copy()
    df_lensa.columns = df_lensa.columns.str.lower().str.strip().str.replace(" ", "_")

    jenis_opsi = sorted(df_lensa['jenis'].dropna().unique().tolist())
    jenis_lensa = st.selectbox("Jenis Lensa", jenis_opsi) if jenis_opsi else ""

    tipe_opsi = sorted(df_lensa[df_lensa['jenis'] == jenis_lensa]['tipe'].dropna().unique().tolist()) if jenis_lensa else []
    tipe_lensa = st.selectbox("Tipe Lensa", tipe_opsi) if tipe_opsi else ""

    merk_opsi = sorted(df_lensa[(df_lensa['jenis'] == jenis_lensa) & (df_lensa['tipe'] == tipe_lensa)]['merk'].dropna().unique().tolist()) if tipe_lensa else []
    merk_lensa = st.selectbox("Merk Lensa", merk_opsi) if merk_opsi else ""

    nama_lensa = ""
    sph_r, cyl_r, axis_r, add_r = "", "", "", ""
    sph_l, cyl_l, axis_l, add_l = "", "", "", ""

    if status_lensa == "Stock":
        st.markdown("### Ukuran Lensa (Stock)")
        sph_list = sorted(df_lensa['sph'].dropna().unique().tolist())
        cyl_list = sorted(df_lensa['cyl'].dropna().unique().tolist())
        add_list = sorted(df_lensa['add'].dropna().unique().tolist())

        colR, colL = st.columns(2)
        with colR:
            sph_r = st.selectbox("SPH R", sph_list, index=sph_list.index("0.00") if "0.00" in sph_list else 0)
            cyl_r = st.selectbox("CYL R", cyl_list, index=cyl_list.index("0.00") if "0.00" in cyl_list else 0)
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
            add_r = st.selectbox("Add R", add_list) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
        with colL:
            sph_l = st.selectbox("SPH L", sph_list, index=sph_list.index("0.00") if "0.00" in sph_list else 0)
            cyl_l = st.selectbox("CYL L", cyl_list, index=cyl_list.index("0.00") if "0.00" in cyl_list else 0)
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
            add_l = st.selectbox("Add L", add_list) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
    else:
        nama_opsi = df_lensa[
            (df_lensa['jenis'] == jenis_lensa) &
            (df_lensa['tipe'] == tipe_lensa) &
            (df_lensa['merk'] == merk_lensa)
        ]['nama_lensa'].dropna().unique().tolist() if merk_lensa else []
        nama_lensa = st.selectbox("Nama Lensa", sorted(nama_opsi)) if nama_opsi else ""

        st.markdown("### Ukuran Lensa (Luar Stock)")
        sph_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-40, 41)]]
        cyl_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-20, 1)]]
        add_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(0, 13)]]

        colR, colL = st.columns(2)
        with colR:
            sph_r = st.selectbox("SPH R", sph_range, index=sph_range.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_range, index=cyl_range.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
            add_r = st.selectbox("Add R", add_range) if tipe_lensa.lower() in ["progressive", "kryptok", "flattop"] else ""
        with colL:
            sph_l = st.selectbox("SPH L", sph_range, index=sph_range.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_range, index=cyl_range.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
            add_l = st.selectbox("Add L", add_range) if tipe_lensa.lower() in ["progressive", "kryptok", "flattop"] else ""

    add_dipakai = add_r if tipe_lensa.lower() in ["progressive", "kryptok", "flattop"] else ""
    harga_lensa = cari_harga_lensa_stock(df_lensa, jenis_lensa, merk_lensa, pakai_reseller=True) if status_lensa == "Stock" else cari_harga_lensa_luar(df_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=True)
    if harga_lensa is None:
        st.warning("Ukuran tidak sesuai rentang harga manapun!")
        st.stop()

    diskon = st.number_input("Diskon Lensa (Rp)", min_value=0, step=500)
    harga_final = harga_lensa - diskon
    potong = st.selectbox("Ongkos Potong", [17000, 27000, 32000])
    ongkir = 25000
    keterangan = st.text_area("Keterangan Tambahan")
    status_kirim = st.radio("Status Kirim", ["Belum Dikirim", "Sudah Dikirim"])
    tanggal_kirim = st.date_input("Tanggal Kirim", value=date.today(), format="DD/MM/YYYY").strftime("%Y-%m-%d") if status_kirim == "Sudah Dikirim" else "-"

    if st.button("📝 Tambah ke Daftar"):
        st.session_state.daftar_item_luar.append({
            "tanggal_ambil": tanggal_ambil,
            "nama": nama,
            "status_lensa": status_lensa,
            "jenis": jenis_lensa,
            "tipe": tipe_lensa,
            "merk": merk_lensa,
            "nama_lensa": nama_lensa,
            "ukuran_r": f"SPH: {sph_r}, CYL: {cyl_r}, Axis: {axis_r}, Add: {add_r}",
            "ukuran_l": f"SPH: {sph_l}, CYL: {cyl_l}, Axis: {axis_l}, Add: {add_l}",
            "harga_lensa": harga_lensa,
            "harga_final": harga_final,
            "diskon": diskon,
            "potong": potong,
            "ongkir": ongkir,
            "keterangan": keterangan,
            "status_kirim": status_kirim,
            "tanggal_kirim": tanggal_kirim
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item_luar:
        st.subheader("📋 Daftar Item")
        df = pd.DataFrame(st.session_state.daftar_item_luar)
        df["subtotal"] = df["harga_final"] + df["potong"] + df["ongkir"]

        for i, item in enumerate(st.session_state.daftar_item_luar):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** {item['merk']} - {item['nama_lensa']} ({item['jenis']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item_luar.pop(i)
                    st.rerun()

        st.dataframe(df, use_container_width=True)
        total = df["subtotal"].sum()
        total = ongkir + total

        st.markdown(f"#### 💰 Total Harga: Rp {total:,.0f}")

        metode = st.selectbox("Jenis Pembayaran", ["Angsuran", "Full"])
        via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"])
        nominal = st.number_input("Masukkan Nominal", min_value=0)
        sisa = nominal - total
        status = "Lunas" if sisa >= 0 else "Belum Lunas"

        if sisa > 0:
            st.success(f"Kembalian: Rp {sisa:,.0f}")

        if st.button("📤 Submit Pesanan"):
            if st.session_state.get("sudah_submit_luar"):
                st.warning("Pesanan sudah dikirim.")
                st.stop()

            try:
                sheet_name = SHEET_NAMES.get('pesanan_luar_kota')
                if sheet_name is None:
                    st.error("Sheet 'pesanan_luar_kota' tidak ditemukan di constants.py")
                    return

                id_transaksi = f"OMSKW/{'01' if nama == 'Nelly' else '02'}/{tanggal_ambil.strftime('%d-%m-%Y')}"
                user = st.session_state.get("user", "Unknown")

                for item in st.session_state.daftar_item_luar:
                    ukuran_r = item['ukuran_r'].split(', ')
                    ukuran_l = item['ukuran_l'].split(', ')

                    row = [
                        today, tanggal_ambil, id_transaksi, item['nama'],
                        item['status_lensa'], item['jenis'], item['tipe'], item['merk'], item['nama_lensa'],
                        ukuran_r[0].split(": ")[1], ukuran_r[1].split(": ")[1], ukuran_r[2].split(": ")[1], ukuran_r[3].split(": ")[1],
                        ukuran_l[0].split(": ")[1], ukuran_l[1].split(": ")[1], ukuran_l[2].split(": ")[1], ukuran_l[3].split(": ")[1],
                        item['harga_lensa'], item['diskon'], item['potong'], item['ongkir'],
                        item['keterangan'], item['status_kirim'], item['tanggal_kirim'],
                        item['harga_final'] + item['potong'] + item['ongkir'], user
                    ]
                    append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['pesanan_luar_kota'], [str(x) for x in row])

                    append_row(SHEET_KEY, JSON_PATH, sheet_name, [str(x) for x in row])

                sheet_pembayaran = SHEET_NAMES.get("pembayaran_luar_kota")
                pembayaran_data = [
                    today, tanggal_ambil, id_transaksi, nama, metode, via,
                    int(total), int(nominal), int(sisa), status, user
                ]
                append_row(SHEET_KEY, JSON_PATH, sheet_pembayaran, [str(x) for x in pembayaran_data])

                st.session_state['sudah_submit_luar'] = True
                st.session_state['ringkasan_luar'] = {
                    'tanggal': today,
                    'nama': nama,
                    'status': status,
                    'sisa': sisa
                }
                del st.session_state.daftar_item_luar
                st.rerun()

            except Exception as e:
                st.error(f"Terjadi kesalahan saat menyimpan: {e}")

    if 'ringkasan_luar' in st.session_state:
        data = st.session_state['ringkasan_luar']
        with st.expander("✅ Pembayaran Berhasil", expanded=True):
            st.markdown(f"""
            **Tanggal Transaksi:** {data['tanggal']}  
            **Nama:** {data['nama']}  
            **Status:** {data['status']}  
            **Sisa/Kembalian:** Rp {data['sisa']:,.0f}
            """)
            if st.button("OK"):
                st.session_state.pop("ringkasan_luar", None)
                st.session_state.pop("sudah_submit_luar", None)
                st.rerun()
