import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils import (
    authorize_gspread, get_dataframe, append_row,
    get_or_create_pelanggan_id, generate_id_transaksi, generate_id_pembayaran,
    cari_harga_lensa_luar, cari_harga_lensa_stock, catat_logframe
)
from constants import SHEET_KEY, SHEET_NAMES
def run():
    @st.cache_data(ttl=300)
    def load_data():
        df_frame = get_dataframe(SHEET_KEY, SHEET_NAMES['dframe'])
        df_lensa_stock = get_dataframe(SHEET_KEY, SHEET_NAMES['dlensa'])
        df_lensa_luar = get_dataframe(SHEET_KEY, SHEET_NAMES['lensa_luar_stock'])

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
    
    import gspread
    from google.oauth2.service_account import Credentials
    client = authorize_gspread()
    worksheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES['dframe'])

    st.title("🧾 Transaksi Kasir")
    today = datetime.today().strftime("%Y-%m-%d,%H:%M:%S")
    tanggal_transaksi = st.date_input("📅 Tanggal Transaksi", value=date.today(), format="DD/MM/YYYY")
    tanggal_str = tanggal_transaksi.strftime("%Y-%m-%d")

    nama = st.text_input("Nama Konsumen")
    kontak = st.text_input("No HP")
    if not nama or not kontak:
        st.warning("Nama dan No HP harus diisi.")
        st.stop()

    nama = str(nama).strip().lower()
    kontak = str(kontak).strip()
    id_pelanggan = get_or_create_pelanggan_id(SHEET_KEY, SHEET_NAMES['pelanggan'], nama, kontak)

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
    if status_lensa == "Stock":
        df_lensa = df_lensa_stock.copy()
        df_lensa.columns = df_lensa.columns.str.lower().str.strip()
    else:
        df_lensa = df_lensa_luar[df_lensa_luar['status'].str.lower() == status_lensa.lower()].copy()
    
   
    jenis_lensa = st.selectbox("Jenis Lensa", sorted(df_lensa['jenis'].dropna().unique()))
    tipe_lensa = st.selectbox("Tipe Lensa", sorted(df_lensa[df_lensa['jenis'] == jenis_lensa]['tipe'].dropna().unique()))
    merk_lensa = st.selectbox("Merk Lensa", sorted(df_lensa[df_lensa['jenis'] == jenis_lensa]['merk'].dropna().unique()))

    # Nama Lensa hanya untuk non-stock
    nama_lensa = ""
    if status_lensa == "Stock":
        st.markdown("**Ukuran Lensa**")     
        colR, colL = st.columns(2)
        # List Ukuran
        sph_list = sorted(df_lensa['sph'].dropna().unique())
        cyl_list = sorted(df_lensa['cyl'].dropna().unique())
        add_list = sorted(df_lensa['add'].dropna().unique())
        
        with colR:
            sph_r = st.selectbox("SPH R", sph_list, index = sph_list.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_list, index = cyl_list.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
            add_r = st.selectbox("Add R", sorted(df_lensa['add'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
        with colL:
            sph_l = st.selectbox("SPH L", sph_list, index = sph_list.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_list, index = cyl_list.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
            add_l = st.selectbox("Add L", sorted(df_lensa['add'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
    
    else:
        df_lensa.columns = df_lensa.columns.str.lower().str.strip().str.replace(" ", "_")
        nama_lensa = st.selectbox("Nama Lensa", sorted(df_lensa[
            (df_lensa['jenis'] == jenis_lensa) & 
            (df_lensa['tipe'] == tipe_lensa) & 
            (df_lensa['merk'] == merk_lensa)
        ]['nama_lensa'].dropna().unique()))
                
        st.markdown("**Ukuran Lensa**")
        colR, colL = st.columns(2)
        # Range Ukuran
        sph_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-40, 41)]]
        cyl_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-20, 1)]]
        add_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(0, 13)]]

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


    # Konversi nilai add (pakai add_r, diasumsikan sama untuk L dan R)
    add_dipakai = add_r if tipe_lensa.lower() in ["progressive", "kryptok", "flattop"] else ""

    if status_lensa == "Stock":
        harga_lensa = cari_harga_lensa_stock(df_lensa, jenis_lensa, merk_lensa)

    else:
        harga_lensa = cari_harga_lensa_luar(df_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=False)
        if harga_lensa is None:
            st.warning("⚠️ Ukuran tidak sesuai rentang harga manapun!")
            st.stop()

    st.markdown("**Pilih Diskon**")
    diskon_mode = st.radio("Jenis Diskon", ["Diskon Persen", "Diskon Lensa"])

    if diskon_mode == "Diskon Persen":
        diskon_persen = st.selectbox("Diskon (%)", [0, 5, 10, 15, 20])
        diskon_lensa = 0
    else:
        diskon_persen = 0
        diskon_lensa = st.number_input("Diskon Lensa (Rp)", min_value=0, step=500)

    # Harga Frame
    if status_frame == "Stock":
        harga_frame = df_frame[(df_frame['Merk'] == merk_frame) & (df_frame['Kode'] == kode_frame)]['Harga Jual'].values[0]
    else:
        harga_frame = 0
    # Diskon
    if diskon_mode == "Diskon Persen":
        diskon_nilai = (harga_frame + harga_lensa) * (diskon_persen / 100)
    else:
        diskon_nilai = diskon_lensa

    harga_setelah_diskon = harga_frame + harga_lensa - diskon_nilai

    # Ringkasan Harga
    st.markdown(f"##### Harga Frame: Rp {harga_frame:,.0f}")
    st.markdown(f"##### Harga lensa: Rp {harga_lensa:,.0f}")

    if st.button("📝 Tambah ke Daftar"):
        st.session_state.daftar_item.append({
            "status_frame": status_frame,
            "merk_frame": merk_frame,
            "kode_frame": kode_frame,
            "status_lensa": status_lensa,
            "jenis_lensa": jenis_lensa,
            "tipe_lensa": tipe_lensa,
            "merk_lensa": merk_lensa,
            "nama_lensa": nama_lensa,
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
        st.dataframe(df, use_container_width=True)

        ribuan_digit = (total // 1000) % 10
        dasar = (total // 10000) * 10000
        harga_final = dasar + 5000 if ribuan_digit >= 5 else dasar
        pembulatan = harga_final - total
        
        st.markdown(f"##### Harga: Rp {total:,.0f}")
        st.markdown(f"##### Pembulatan: Rp {pembulatan:,.0f}")
        st.markdown(f"#### 💰 Total Harga: Rp {harga_final:,.0f}")

        metode = st.selectbox("Jenis Pembayaran", ["Angsuran", "Full"])
        via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"])
        nominal = st.number_input("Masukkan Nominal", min_value=0)
        sisa = nominal - harga_final
        status = "Lunas" if sisa >= 0 else "Belum Lunas"

        if sisa > 0:
            st.success(f"Kembalian: Rp {sisa:,.0f}")

        if st.button("💾 Simpan Pembayaran"):
            id_transaksi = generate_id_transaksi(SHEET_KEY, SHEET_NAMES['transaksi'], tanggal_transaksi)
            id_pembayaran = generate_id_pembayaran(SHEET_KEY, SHEET_NAMES['pembayaran'], tanggal_transaksi)
            user = st.session_state.get("user", "Unknown")

            for item in st.session_state.daftar_item:
                row = [today, tanggal_str, id_transaksi, id_pelanggan, nama,
                    item['status_frame'], item['merk_frame'], item['kode_frame'],
                    item['status_lensa'], item['jenis_lensa'], item['tipe_lensa'], item['merk_lensa'], item['nama_lensa'],
                    item['sph_r'], item['cyl_r'], item['axis_r'], item['add_r'],
                    item['sph_l'], item['cyl_l'], item['axis_l'], item['add_l'],
                    item['harga_frame'], item['harga_lensa'], int(item['diskon']), int(item['subtotal']), user]
                append_row(SHEET_KEY, SHEET_NAMES['transaksi'], [str(x) for x in row])
                
                # Catat log frame
                if item['status_frame'] == "Stock":
                    catat_logframe(
                        sheet_key=SHEET_KEY,
                        sheet_name="log_frame",
                        merk=item['merk_frame'],
                        kode=item['kode_frame'],
                        source="kasir",
                        status_frame=item['status_frame'],
                        id_transaksi=id_transaksi,
                        nama=nama,
                        user=user
                    )                
                
                # Kurangi Stock Frame
                if item['status_frame'] == "Stock":
                    kondisi = (
                        (df_frame['Merk'] == item['merk_frame']) &
                        (df_frame['Kode'] == item['kode_frame'])
                    )

                    if kondisi.any():
                        idx = kondisi.idxmax()
                        row_excel = idx + 2
                        stock_lama = int(str(df_frame.at[idx, 'Stock']).replace(",", "").strip())
                        stock_baru = max(0, stock_lama - 1)
                        worksheet.update_cell(row_excel, df_frame.columns.get_loc("Stock") + 1, stock_baru)
                        df_frame.at[idx, 'Stock'] = stock_baru

            df_pembayaran = get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran'])
            pembayaran_ke = df_pembayaran[df_pembayaran['ID Transaksi'] == id_transaksi].shape[0] + 1

            pembayaran_data = [
                today, id_transaksi, id_pembayaran, id_pelanggan,
                tanggal_str, nama, kontak, metode, via,
                str(int(harga_final)), str(int(nominal)), str(int(sisa)), status,
                str(pembayaran_ke), user
            ]
            append_row(SHEET_KEY, SHEET_NAMES['pembayaran'], pembayaran_data)

            st.cache_data.clear()
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

