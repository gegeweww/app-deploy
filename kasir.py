import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    authorize_gspread, get_dataframe, append_row, append_rows,
    get_or_create_pelanggan_id, generate_id_transaksi, generate_id_pembayaran,
    cari_harga_lensa_luar, cari_harga_lensa_stock, catat_logframe, catat_loglensa
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
        df_lensa_luar.columns = df_lensa_luar.columns.str.strip().str.replace(" ", "_")
        df_lensa_stock.columns = df_lensa_stock.columns.str.strip().str.replace(" ", "_")

        return df_frame, df_lensa_stock, df_lensa_luar

    df_frame, df_lensa_stock, df_lensa_luar = load_data()
    
    
    def format_2digit(val):
        try:
            return f"{float(val):.2f}"
        except Exception:
            return str(val).strip() if val is not None else ""
        
    df_lensa_stock['SPH'] = df_lensa_stock['SPH'].apply(format_2digit)
    df_lensa_stock['CYL'] = df_lensa_stock['CYL'].apply(format_2digit)
    df_lensa_stock['ADD'] = df_lensa_stock['ADD'].apply(format_2digit)
    for col in ['Jenis', 'Tipe', 'Merk']:
        df_lensa_stock[col] = df_lensa_stock[col].astype(str).str.strip()
    
    import gspread
    from google.oauth2.service_account import Credentials
    
    @st.cache_resource
    def get_worksheets():
        client = authorize_gspread()
        spreadsheet = client.open_by_key(SHEET_KEY)
        return {
            'frame': spreadsheet.worksheet(SHEET_NAMES['dframe']),
            'lensa': spreadsheet.worksheet(SHEET_NAMES['dlensa']),
        }
    worksheets = get_worksheets()
    worksheet_frame = worksheets['frame']
    worksheet_lensa = worksheets['lensa']

    st.title("🧾 Transaksi Kasir")
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y, %H:%M:%S")
    tanggal_transaksi = st.date_input("📅 Tanggal Transaksi", value=date.today(), format="DD/MM/YYYY")
    tanggal_str = tanggal_transaksi.strftime("%d-%m-%Y")

    nama = st.text_input("Nama Konsumen", key="nama_konsumen")
    kontak = st.text_input("No HP", key="no_hp")
    if not nama or not kontak:
        st.warning("Nama dan No HP harus diisi.")
        st.stop()

    @st.cache_data(ttl=300)
    def cached_get_or_create_pelanggan_id(sheet_key, sheet_name, nama, kontak):
        return get_or_create_pelanggan_id(sheet_key, sheet_name, nama, kontak)

    nama = str(nama).strip().lower()
    kontak = str(kontak).strip()
    id_pelanggan = cached_get_or_create_pelanggan_id(SHEET_KEY, SHEET_NAMES['pelanggan'], nama, kontak)

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
        # Tipe Lensa
        tipe_option = sorted(df_lensa['Tipe'].dropna().unique())
        tipe_lensa = st.selectbox("Tipe Lensa", tipe_option)
        # Merk Lensa
        df_merk = df_lensa[df_lensa['Tipe'] == tipe_lensa]
        merk_option = sorted(df_merk['Merk'].dropna().unique())
        merk_lensa = st.selectbox("Merk Lensa", merk_option)
        # Jenis Lensa
        df_jenis = df_lensa[(df_lensa['Tipe'] == tipe_lensa) & (df_lensa['Merk'] == merk_lensa)]
        jenis_option = sorted(df_jenis['Jenis'].dropna().unique())
        jenis_lensa = st.selectbox("Jenis Lensa", jenis_option)
    else:
        df_lensa = df_lensa_luar[df_lensa_luar['Status'] == status_lensa].copy()
        # Tipe Lensa
        tipe_option = sorted(df_lensa['Tipe'].dropna().unique())
        tipe_lensa = st.selectbox("Tipe Lensa", tipe_option)
        # Merk Lensa
        df_merk = df_lensa[df_lensa['Tipe'] == tipe_lensa]
        merk_option = sorted(df_merk['Merk'].dropna().unique())
        merk_lensa = st.selectbox("Merk Lensa", merk_option)
        # Jenis Lensa
        df_jenis = df_lensa[(df_lensa['Tipe'] == tipe_lensa) & (df_lensa['Merk'] == merk_lensa)]
        jenis_option = sorted(df_jenis['Jenis'].dropna().unique())
        jenis_lensa = st.selectbox("Jenis Lensa", jenis_option)
    # Nama Lensa hanya untuk non-stock
    nama_lensa = ""
    if status_lensa == "Stock":
        st.markdown("**Ukuran Lensa**")     
        colR, colL = st.columns(2)
        # List Ukuran
        sph_list = sorted(df_lensa['SPH'].dropna().unique())
        cyl_list = sorted(df_lensa['CYL'].dropna().unique())
        add_list = sorted(df_lensa['ADD'].dropna().unique())

        with colR:
            sph_r = st.selectbox("SPH R", sph_list, index = sph_list.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_list, index = cyl_list.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
            add_r = st.selectbox("Add R", sorted(df_lensa['ADD'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
        with colL:
            sph_l = st.selectbox("SPH L", sph_list, index = sph_list.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_list, index = cyl_list.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
            add_l = st.selectbox("Add L", sorted(df_lensa['ADD'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
    
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
            add_r = st.selectbox("Add R", add_range) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""

        with colL:
            sph_l = st.selectbox("SPH L", sph_range, index=sph_range.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_range, index=cyl_range.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
            add_l = st.selectbox("Add L", add_range) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""


    # Konversi nilai add (pakai add_r, diasumsikan sama untuk L dan R)
    add_dipakai = add_r if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
    if status_lensa == "Stock":
        harga_lensa = cari_harga_lensa_stock(df_lensa, tipe_lensa, jenis_lensa, merk_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=False)
        if harga_lensa is None:
            st.warning("⚠️ Harga lensa stock tidak ditemukan!")
            st.stop()

    else:
        harga_lensa = cari_harga_lensa_luar(df_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=False)
        if harga_lensa is None:
            st.warning("⚠️ Ukuran tidak sesuai rentang harga manapun!")
            st.stop()

    tambahan = st.number_input("Biaya Tambahan (Rp)", min_value=0, step=5000, value=0)
    
    st.markdown("**Pilih Diskon**")
    diskon_mode = st.radio("Jenis Diskon", ["Diskon Persen", "Diskon Harga"])

    if diskon_mode == "Diskon Persen":
        diskon_persen = st.selectbox("Diskon (%)", [0, 5, 10, 15, 20])
        diskon_harga = 0
    else:
        diskon_persen = 0
        diskon_harga = st.number_input("Diskon Harga (Rp)", min_value=0, step=500, value=0)

    # Harga Frame
    if status_frame == "Stock":
        harga_frame = df_frame[(df_frame['Merk'] == merk_frame) & (df_frame['Kode'] == kode_frame)]['Harga Jual'].values[0]
    else:
        harga_frame = 0
    # Diskon
    harga_frame = int(harga_frame or 0)
    tambahan = int(tambahan or 0)
        
    if diskon_mode == "Diskon Persen":
        diskon_nilai = float((harga_frame + harga_lensa + tambahan) * (diskon_persen / 100))
    else:
        diskon_nilai = diskon_harga
    diskon_nilai = int(diskon_nilai or 0)
    # Total Harga Setelah Diskon
    harga_setelah_diskon = harga_frame + harga_lensa - diskon_nilai

    # Ringkasan Harga
    st.markdown(f"##### Harga Frame: Rp {harga_frame:,.0f}")
    st.markdown(f"##### Harga lensa: Rp {harga_lensa:,.0f}")

    if st.button("📝 Tambah ke Daftar"):
    # ===================== CEK SEMUA STOK DULU =====================
        # --- Cek stok frame ---
        if status_frame == "Stock":
            kondisi = (
                (df_frame['Merk'] == merk_frame) &
                (df_frame['Kode'] == kode_frame)
            )
            if kondisi.any():
                idx = kondisi.idxmax()
                stock_lama = int(str(df_frame.at[idx, 'Stock']).replace(",", "").strip())
                if stock_lama == 0:
                    st.warning(f"Stock frame {merk_frame} {kode_frame} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
        # --- Cek stok lensa kanan ---
        if status_lensa == "Stock":
            if tipe_lensa.lower() == 'single vision':
                kondisi_kanan = (
                    (df_lensa_stock['Jenis'] == jenis_lensa) &
                    (df_lensa_stock['Tipe'] == tipe_lensa) &
                    (df_lensa_stock['Merk'] == merk_lensa) &
                    (df_lensa_stock['SPH'] == sph_r) &
                    (df_lensa_stock['CYL'] == cyl_r)
                )
            else:
                kondisi_kanan = (
                    (df_lensa_stock['Jenis'] == jenis_lensa) &
                    (df_lensa_stock['Tipe'] == tipe_lensa) &
                    (df_lensa_stock['Merk'] == merk_lensa) &
                    (df_lensa_stock['SPH'] == sph_r) &
                    (df_lensa_stock['CYL'] == cyl_r) &
                    (df_lensa_stock['ADD'] == add_r)
                )
            if kondisi_kanan.any():
                idx = kondisi_kanan.idxmax()
                stock_val = df_lensa_stock.at[idx, 'Stock']
                try:
                    stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                except Exception:
                    stock_lama = 0
                if stock_lama == 0:
                    st.warning(f"Stock lensa {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph_r} CYL {cyl_r} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
        # --- Cek stok lensa kiri ---
        if status_lensa == "Stock":
            if tipe_lensa.lower() == 'single vision':
                kondisi_kiri = (
                    (df_lensa_stock['Jenis'] == jenis_lensa) &
                    (df_lensa_stock['Tipe'] == tipe_lensa) &
                    (df_lensa_stock['Merk'] == merk_lensa) &
                    (df_lensa_stock['SPH'] == sph_l) &
                    (df_lensa_stock['CYL'] == cyl_l)
                )
            else:
                kondisi_kiri = (
                    (df_lensa_stock['Jenis'] == jenis_lensa) &
                    (df_lensa_stock['Tipe'] == tipe_lensa) &
                    (df_lensa_stock['Merk'] == merk_lensa) &
                    (df_lensa_stock['SPH'] == sph_l) &
                    (df_lensa_stock['CYL'] == cyl_l) &
                    (df_lensa_stock['ADD'] == add_l)
                )
            if kondisi_kiri.any():
                idx = kondisi_kiri.idxmax()
                stock_val = df_lensa_stock.at[idx, 'Stock']
                try:
                    stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                except Exception:
                    stock_lama = 0
                if stock_lama == 0:
                    st.warning(f"Stock lensa {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph_l} CYL {cyl_l} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
                        
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
            "tambahan": tambahan,
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
        via = st.selectbox("Via Pembayaran", ["Cash", "Qris EDC Mandiri", "Qris EDC BCA", "Qris Statis Mandiri", "TF BCA", "TF Mandiri"])
        nominal = st.number_input("Masukkan Nominal", min_value=0, step=1000)
        sisa = nominal - harga_final
        status = "Lunas" if sisa >= 0 else "Belum Lunas"

        if sisa > 0:
            st.success(f"Kembalian: Rp {sisa:,.0f}")

        if st.button("💾 Simpan Pembayaran"):
            st.session_state['simpan_pembayaran'] = True
            
    # ===================== JIKA SEMUA STOK AMAN, LANJUTKAN =====================
    if st.session_state.get('simpan_pembayaran', False):
        id_transaksi = generate_id_transaksi(SHEET_KEY, SHEET_NAMES['transaksi'], tanggal_transaksi)
        id_pembayaran = generate_id_pembayaran(SHEET_KEY, SHEET_NAMES['pembayaran'], tanggal_transaksi)
        user = st.session_state.get("user", "Unknown")

        # Normalisasi data item
        sph_r = format_2digit(item['sph_r'])
        cyl_r = format_2digit(item['cyl_r'])
        add_r = format_2digit(item['add_r']) if item['add_r'] else ""
        sph_l = format_2digit(item['sph_l'])
        cyl_l = format_2digit(item['cyl_l'])
        add_l = format_2digit(item['add_l']) if item['add_l'] else ""

        # Simpan transaksi
        rows_transaksi = []
        for item in st.session_state.daftar_item:
            row = [today, tanggal_str, id_transaksi, id_pelanggan, nama,
                item['status_frame'], item['merk_frame'], item['kode_frame'],
                item['status_lensa'], item['jenis_lensa'], item['tipe_lensa'], item['merk_lensa'], item['nama_lensa'],
                item['sph_r'], item['cyl_r'], item['axis_r'], item['add_r'],
                item['sph_l'], item['cyl_l'], item['axis_l'], item['add_l'],
                item['harga_frame'], item['harga_lensa'], item['tambahan'], int(item['diskon']), int(item['subtotal']), user
            ]
            rows_transaksi.append([str(x) for x in row])
        try:
            append_rows(SHEET_KEY, SHEET_NAMES['transaksi'], rows_transaksi)
        except Exception as e:
            st.error(f"Gagal simpan transaksi: {e}")
            st.session_state['simpan_pembayaran'] = False
            st.stop()

        # Catat log frame & lensa, update stok frame & lensa
        for item in st.session_state.daftar_item:
            # Log frame
            if item['status_frame'] == "Stock":
                catat_logframe(
                    sheet_key=SHEET_KEY,
                    sheet_name="logframe",
                    merk=item['merk_frame'],
                    kode=item['kode_frame'],
                    source="kasir",
                    status_frame=item['status_frame'],
                    id_transaksi=id_transaksi,
                    nama=nama,
                    user=user
                )
            # Log lensa kanan
            if item['status_lensa'] == "Stock":
                catat_loglensa(
                    sheet_key=SHEET_KEY,
                    sheet_name="loglensa",
                    merk=item['merk_lensa'],
                    tipe=item['tipe_lensa'],
                    jenis=item['jenis_lensa'],
                    sph=item['sph_r'],
                    cyl=item['cyl_r'],
                    add=item['add_r'],
                    source="kasir",
                    status_lensa=item['status_lensa'],
                    id_transaksi=id_transaksi,
                    nama=nama,
                    user=user
                )
            # Log lensa kiri
            if item['status_lensa'] == "Stock":
                catat_loglensa(
                    sheet_key=SHEET_KEY,
                    sheet_name="loglensa",
                    merk=item['merk_lensa'],
                    tipe=item['tipe_lensa'],
                    jenis=item['jenis_lensa'],
                    sph=item['sph_l'],
                    cyl=item['cyl_l'],
                    add=item['add_l'],
                    source="kasir",
                    status_lensa=item['status_lensa'],
                    id_transaksi=id_transaksi,
                    nama=nama,
                    user=user
                )
            # Update stok frame
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
                    try:
                        col_Stock = worksheet_frame.find("Stock").col
                        worksheet_frame.update_cell(row_excel, col_Stock, stock_baru)
                        df_frame.at[idx, 'Stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock frame: {e}")
            # Update stok lensa kanan
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kanan = (
                        (df_lensa_stock['Jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['Tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['Merk'] == item['merk_lensa']) &
                        (df_lensa_stock['SPH'] == format_2digit(item['sph_r'])) &
                        (df_lensa_stock['CYL'] == format_2digit(item['cyl_r']))
                    )
                else:
                    add_r = str(item['add_r']).strip() if item['add_r'] else ""
                    kondisi_kanan = (
                        (df_lensa_stock['Jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['Tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['Merk'] == item['merk_lensa']) &
                        (df_lensa_stock['SPH'] == format_2digit(item['sph_r'])) &
                        (df_lensa_stock['CYL'] == format_2digit(item['cyl_r'])) &
                        (df_lensa_stock['ADD'] == add_r)
                    )
                if kondisi_kanan.any():
                    idx = kondisi_kanan.idxmax()
                    row_excel = idx + 2
                    stock_val = df_lensa_stock.at[idx, 'Stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    stock_baru = max(0, stock_lama - 1)
                    try:
                        col_stock = worksheet_lensa.find("Stock").col
                        worksheet_lensa.update_cell(row_excel, col_stock, stock_baru)
                        df_lensa_stock.at[idx, 'Stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock lensa kanan: {e}")
            # Update stok lensa kiri
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kiri = (
                        (df_lensa_stock['Jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['Tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['Merk'] == item['merk_lensa']) &
                        (df_lensa_stock['SPH'] == format_2digit(item['sph_l'])) &
                        (df_lensa_stock['CYL'] == format_2digit(item['cyl_l']))
                    )
                else:
                    add_l = str(item['add_l']).strip() if item['add_l'] else ""
                    kondisi_kiri = (
                        (df_lensa_stock['Jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['Tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['Merk'] == item['merk_lensa']) &
                        (df_lensa_stock['SPH'] == format_2digit(item['sph_l'])) &
                        (df_lensa_stock['CYL'] == format_2digit(item['cyl_l'])) &
                        (df_lensa_stock['ADD'] == add_l)
                    )
                if kondisi_kiri.any():
                    idx = kondisi_kiri.idxmax()
                    row_excel = idx + 2
                    stock_val = df_lensa_stock.at[idx, 'Stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    stock_baru = max(0, stock_lama - 1)
                    try:
                        col_stock = worksheet_lensa.find("Stock").col
                        worksheet_lensa.update_cell(row_excel, col_stock, stock_baru)
                        df_lensa_stock.at[idx, 'Stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock lensa kiri: {e}")

        # Simpan pembayaran
        @st.cache_data(ttl=300)
        def load_pembayaran():
            return get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran'])

        df_pembayaran = load_pembayaran()
        pembayaran_ke = df_pembayaran[df_pembayaran['ID Transaksi'] == id_transaksi].shape[0] + 1

        pembayaran_data = [
            today, id_transaksi, id_pembayaran, id_pelanggan,
            tanggal_str, nama, kontak, metode, via,
            str(int(harga_final)), str(int(nominal)), str(int(sisa)), status,
            str(pembayaran_ke), user
        ]
        append_row(SHEET_KEY, SHEET_NAMES['pembayaran'], pembayaran_data)
        st.session_state['ringkasan_tersimpan'] = {
            'id_transaksi': id_transaksi,
            'tanggal': today,
            'nama': nama.title(),
            'status': status,
            'sisa': sisa
        }
        st.session_state['simpan_pembayaran'] = False
        st.rerun()

    def reset_form_kasir():
        st.session_state.pop("daftar_item", None)
        st.session_state.pop("simpan_pembayaran", None)
        st.session_state.pop("ringkasan_tersimpan", None)
        st.session_state.pop("nama_konsumen", None)
        st.session_state.pop("no_hp", None)

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
                reset_form_kasir()
                st.rerun()
