import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    authorize_gspread, get_dataframe, append_row, append_rows, catat_loglensa,
    cari_harga_lensa_luar, cari_harga_lensa_stock,
    generate_id_skw, generate_id_pemb_skw
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
        
    @st.cache_resource
    def get_worksheets():
        client = authorize_gspread()
        spreadsheet = client.open_by_key(SHEET_KEY)
        return {
            'lensastock': spreadsheet.worksheet(SHEET_NAMES['dlensa']),
            'lensaluar': spreadsheet.worksheet(SHEET_NAMES['lensa_luar_stock'])
        }
    worksheets = get_worksheets()
    worksheet_lensa_stock = worksheets['lensastock']
    worksheet_lensa_luar = worksheets['lensaluar']

    st.title("📦 Pesanan Luar Kota")
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y, %H:%M:%S")
    colL, colR = st.columns(2)
    with colL:
        tanggal_ambil = st.date_input("📅 Tanggal Ambil", value=date.today(), format="DD/MM/YYYY")
        tanggal_ambil = tanggal_ambil.strftime("%d-%m-%Y")
    with colR:
        nama = st.selectbox("Nama Konsumen", ["Rahmat", "Nelly"])

    if "daftar_item_luar" not in st.session_state:
        st.session_state.daftar_item_luar = []

    st.subheader("➕ Tambah Item")

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
        harga_lensa = cari_harga_lensa_stock(df_lensa, tipe_lensa, jenis_lensa, merk_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=True)
        if harga_lensa is None:
            st.warning("⚠️ Harga lensa stock tidak ditemukan!")
            st.stop()

    else:
        harga_lensa = cari_harga_lensa_luar(df_lensa, tipe_lensa, jenis_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, False)
        if harga_lensa is None:
            st.warning("⚠️ Ukuran tidak sesuai rentang harga manapun!")
            st.stop()
    
    # Ringkasan Harga
    st.markdown(f"#### Harga lensa: Rp {harga_lensa:,.0f}")        
    diskon = st.number_input("Diskon Lensa (Rp)", min_value=0, step=1000)
    tambahan = st.number_input("Tambahan (Rp)", min_value=0, step=1000)
    potong = st.selectbox("Ongkos Potong", [17000, 27000, 32000])
    ongkir = 25000
    subtotal = (harga_lensa + potong + ongkir + tambahan)
    keterangan = st.text_area("Keterangan Tambahan")

    if st.button("📝 Tambah ke Daftar"):
    # ===================== CEK SEMUA STOK DULU =====================
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

        st.session_state.daftar_item_luar.append({
            "tanggal_ambil": tanggal_ambil,
            "nama": nama,
            "status_lensa": status_lensa,
            "jenis_lensa": jenis_lensa,
            "tipe_lensa": tipe_lensa,
            "merk_lensa": merk_lensa,
            "nama_lensa": nama_lensa,
            "sph_r": sph_r, "cyl_r": cyl_r, "axis_r": axis_r, "add_r": add_r,
            "sph_l": sph_l, "cyl_l": cyl_l, "axis_l": axis_l, "add_l": add_l,
            "harga_lensa": harga_lensa,
            "potong": potong,
            "ongkir": ongkir,
            "tambahan": tambahan,
            "subtotal": subtotal,
            "diskon": diskon,
            "keterangan": keterangan,
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item_luar:
        st.subheader("📋 Daftar Item")
        df = pd.DataFrame(st.session_state.daftar_item_luar)
        df["Total"] = df["subtotal"] - df["diskon"]

        for i, item in enumerate(st.session_state.daftar_item_luar):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** {item['merk_lensa']} - {item['nama_lensa']} ({item['jenis_lensa']}, {item['tipe_lensa']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item_luar.pop(i)
                    st.rerun()

        df = df.rename(columns={
            "tanggal_ambil": "Tanggal Ambil",
            "nama": "Nama",
            "status_lensa": "Status Lensa",
            "jenis_lensa": "Jenis Lensa",
            "tipe_lensa": "Tipe Lensa",
            "merk_lensa": "Merk Lensa",
            "nama_lensa": "Nama Lensa",
            "sph_r": "SPH R", "cyl_r": "CYL R", "axis_r": "Axis R", "add_r": "Add R",
            "sph_l": "SPH L", "cyl_l": "CYL L", "axis_l": "Axis L", "add_l": "Add L",
            "harga_lensa": "Harga Lensa",
            "potong": "Ongkos Potong",
            "ongkir": "Ongkos Kirim",
            "tambahan": "Tambahan",
            "subtotal": "Subtotal",
            "diskon": "Diskon",
            "Total": "Total",
            "keterangan": "Keterangan"
        })

        st.dataframe(df, use_container_width=True)
        total = df["Total"].sum()

        st.markdown(f"#### 💰 Total Harga: Rp {total:,.0f}")

        metode = st.selectbox("Jenis Pembayaran", ["Angsuran", "Full"])
        via = st.selectbox("Via Pembayaran", ["Cash", "TF BCA", "TF Mandiri"])
        nominal = st.number_input("Masukkan Nominal", min_value=0)
        if nominal > 0:
            tanggal_bayar = st.date_input("📅 Tanggal Bayar", value=date.today(), format="DD/MM/YYYY").strftime("%d-%m-%Y")
        else:
            tanggal_bayar = "-"
        sisa = nominal - total
        status = "Lunas" if sisa >= 0 else "Belum Lunas"

        if sisa > 0:
            st.success(f"Kembalian: Rp {sisa:,.0f}")

        if st.button("📤 Submit Pembayaran"):
            st.session_state['simpan_pembayaran'] = True

    # ===================== JIKA SEMUA STOK AMAN, LANJUTKAN =====================
    if st.session_state.get('simpan_pembayaran', False):
        id_transaksi = generate_id_skw(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], nama, tanggal_ambil)
        id_pembayaran = generate_id_pemb_skw(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], nama, tanggal_ambil)
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
        for item in st.session_state.daftar_item_luar:
            row = [
                today, tanggal_ambil, id_transaksi, item['nama'],
                item['status_lensa'], item['jenis_lensa'], item['tipe_lensa'], item['merk_lensa'], item['nama_lensa'],
                item['sph_r'], item['cyl_r'], item['axis_r'], item['add_r'],
                item['sph_l'], item['cyl_l'], item['axis_l'], item['add_l'],
                item['harga_lensa'], item['potong'], item['ongkir'], item['tambahan'], item['diskon'],
                item['keterangan'], item['subtotal'] - item['diskon'], user
            ]
            rows_transaksi.append([str(x) for x in row])
        try:
            append_rows(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], rows_transaksi)
        except Exception as e:
            st.error(f"Gagal simpan transaksi: {e}")
            st.session_state['simpan_pembayaran'] = False
            st.stop()

        # Catat log lensa, update stok lensa
        for item in st.session_state.daftar_item_luar:
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
                    source="luarkota",
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
                    source="luarkota",
                    status_lensa=item['status_lensa'],
                    id_transaksi=id_transaksi,
                    nama=nama,
                    user=user
                )
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
                        col_stock = worksheet_lensa_stock.find("Stock").col
                        worksheet_lensa_stock.update_cell(row_excel, col_stock, stock_baru)
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
                        col_stock = worksheet_lensa_stock.find("Stock").col
                        worksheet_lensa_stock.update_cell(row_excel, col_stock, stock_baru)
                        df_lensa_stock.at[idx, 'Stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock lensa kiri: {e}")
 
        # Simpan pembayaran
        @st.cache_data(ttl=300)
        def load_pembayaran():
            return get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'])

        df_pembayaran = load_pembayaran()
        pembayaran_ke = df_pembayaran[df_pembayaran['Id Transaksi'] == id_transaksi].shape[0] + 1
        tanggal_bayar = tanggal_ambil
        pembayaran_data = [
            today, tanggal_ambil, tanggal_bayar, id_transaksi, id_pembayaran, nama, metode, via,
            int(total), int(nominal), int(sisa), pembayaran_ke, tanggal_bayar, status, user
        ]
        append_row(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'], [str(x) for x in pembayaran_data])
        st.session_state['ringkasan_tersimpan'] = {
            'id_transaksi': id_transaksi,
            'tanggal': today,
            'nama': nama.title(),
            'status': status,
            'sisa': sisa
        }
        st.session_state['simpan_pembayaran'] = False
        st.rerun()

    def reset_form_luarkota():
        st.session_state.pop("daftar_item_luar", None)
        st.session_state.pop("simpan_pembayaran", None)
        st.session_state.pop("ringkasan_tersimpan", None)

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
                reset_form_luarkota()
                st.rerun()
