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
        df_lensa_luar.columns = df_lensa_luar.columns.str.lower().str.strip().str.replace(" ", "_")
        df_lensa_stock.columns = df_lensa_stock.columns.str.strip().str.lower().str.replace(" ", "_")
        return df_frame, df_lensa_stock, df_lensa_luar

    df_frame, df_lensa_stock, df_lensa_luar = load_data()

    def format_2digit(val):
        try:
            return f"{float(val):.2f}"
        except Exception:
            return str(val).strip() if val is not None else ""

    df_lensa_stock['sph'] = df_lensa_stock['sph'].apply(format_2digit)
    df_lensa_stock['cyl'] = df_lensa_stock['cyl'].apply(format_2digit)
    df_lensa_stock['add'] = df_lensa_stock['add'].apply(format_2digit)
    for col in ['jenis', 'tipe', 'merk']:
        df_lensa_stock[col] = df_lensa_stock[col].astype(str).str.lower().str.strip()
        
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
    df_lensa = df_lensa_stock.copy() if status_lensa == "Stock" else df_lensa_luar[df_lensa_luar['status'].str.lower() == status_lensa.lower()].copy()
    df_lensa.columns = df_lensa.columns.str.lower().str.strip().str.replace(" ", "_")

    jenis_opsi = sorted(df_lensa['jenis'].dropna().unique().tolist())
    jenis_lensa = st.selectbox("Jenis Lensa", jenis_opsi) if jenis_opsi else ""

    tipe_opsi = sorted(df_lensa[df_lensa['jenis'] == jenis_lensa]['tipe'].dropna().unique().tolist()) if jenis_lensa else []
    tipe_lensa = st.selectbox("Tipe Lensa", tipe_opsi) if tipe_opsi else ""

    merk_opsi = sorted(df_lensa[(df_lensa['jenis'] == jenis_lensa) & (df_lensa['tipe'] == tipe_lensa)]['merk'].dropna().unique().tolist()) if tipe_lensa else []
    merk_lensa = st.selectbox("Merk Lensa", merk_opsi) if merk_opsi else ""

    nama_lensa = None
    sph_r, cyl_r, axis_r, add_r = None, None, None, None
    sph_l, cyl_l, axis_l, add_l = None, None, None, None

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

    if st.button("📝 Tambah ke Daftar"):
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
            "harga_final": harga_final,
            "diskon": diskon,
            "potong": potong,
            "ongkir": ongkir,
            "keterangan": keterangan,
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item_luar:
        st.subheader("📋 Daftar Item")
        df = pd.DataFrame(st.session_state.daftar_item_luar)
        df["subtotal"] = df["harga_final"] + df["potong"] + df["ongkir"]

        for i, item in enumerate(st.session_state.daftar_item_luar):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** {item['merk_lensa']} - {item['nama_lensa']} ({item['jenis_lensa']}, {item['tipe_lensa']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item_luar.pop(i)
                    st.rerun()

        st.dataframe(df, use_container_width=True)
        total = df["subtotal"].sum()

        st.markdown(f"#### 💰 Total Harga: Rp {total:,.0f}")

        metode = st.selectbox("Jenis Pembayaran", ["Angsuran", "Full"])
        via = st.selectbox("Via Pembayaran", ["Cash", "TF", "Qris"])
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

    # ===================== CEK SEMUA STOK DULU =====================
    if st.session_state.get('simpan_pembayaran', False):
        # Cek stock lensa semua item
        for item in st.session_state.daftar_item_luar:
            sph_r = format_2digit(item['sph_r'])
            cyl_r = format_2digit(item['cyl_r'])
            add_r = format_2digit(item['add_r']) if item['add_r'] else ""
            sph_l = format_2digit(item['sph_l'])
            cyl_l = format_2digit(item['cyl_l'])
            add_l = format_2digit(item['add_l']) if item['add_l'] else ""
    
            # --- Cek stok lensa kanan ---
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kanan = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == item['sph_r']) &
                        (df_lensa_stock['cyl'] == item['cyl_r'])
                    )
                else:
                    kondisi_kanan = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == item['sph_r']) &
                        (df_lensa_stock['cyl'] == item['cyl_r']) &
                        (df_lensa_stock['add'] == item['add_r'])
                    )
                if kondisi_kanan.any():
                    idx = kondisi_kanan.idxmax()
                    stock_val = df_lensa_stock.at[idx, 'stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    if stock_lama == 0:
                        st.warning(f"Stock lensa {item['merk_lensa']} {item['tipe_lensa']} {item['jenis_lensa']} SPH {item['sph_r']} CYL {item['cyl_r']} sudah habis!")
                        st.session_state['simpan_pembayaran'] = False
                        st.stop()
            # --- Cek stok lensa kiri ---
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kiri = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == item['sph_l']) &
                        (df_lensa_stock['cyl'] == item['cyl_l'])
                    )
                else:
                    kondisi_kiri = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == item['sph_l']) &
                        (df_lensa_stock['cyl'] == item['cyl_l']) &
                        (df_lensa_stock['add'] == item['add_l'])
                    )
                if kondisi_kiri.any():
                    idx = kondisi_kiri.idxmax()
                    stock_val = df_lensa_stock.at[idx, 'stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    if stock_lama == 0:
                        st.warning(f"Stock lensa {item['merk_lensa']} {item['tipe_lensa']} {item['jenis_lensa']} SPH {item['sph_l']} CYL {item['cyl_l']} sudah habis!")
                        st.session_state['simpan_pembayaran'] = False
                        st.stop()

        # ===================== JIKA SEMUA STOK AMAN, LANJUTKAN =====================

        id_transaksi = generate_id_skw(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], nama, tanggal_ambil)
        id_pembayaran = generate_id_pemb_skw(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], nama, tanggal_ambil)
        user = st.session_state.get("user", "Unknown")

        # Simpan transaksi
        rows_transaksi = []
        for item in st.session_state.daftar_item_luar:
            row = [
                today, tanggal_ambil, id_transaksi, item['nama'],
                item['status_lensa'], item['jenis_lensa'], item['tipe_lensa'], item['merk_lensa'], item['nama_lensa'],
                item['sph_r'], item['cyl_r'], item['axis_r'], item['add_r'],
                item['sph_l'], item['cyl_l'], item['axis_l'], item['add_l'],
                item['harga_lensa'], item['diskon'], item['potong'], item['ongkir'],
                item['keterangan'], item['harga_final'] + item['potong'] + item['ongkir'], user
            ]
            rows_transaksi.append([str(x) for x in row])
        try:
            append_rows(SHEET_KEY, SHEET_NAMES['pesanan_luar_kota'], rows_transaksi)
        except Exception as e:
            st.error(f"Gagal simpan transaksi: {e}")
            st.session_state['simpan_pembayaran'] = False
            st.stop()

        # Catat log frame & lensa, update stok frame & lensa
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
            # Update stok lensa kanan
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kanan = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == format_2digit(item['sph_r'])) &
                        (df_lensa_stock['cyl'] == format_2digit(item['cyl_r']))
                    )
                else:
                    add_r = str(item['add_r']).strip() if item['add_r'] else ""
                    kondisi_kanan = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == format_2digit(item['sph_r'])) &
                        (df_lensa_stock['cyl'] == format_2digit(item['cyl_r'])) &
                        (df_lensa_stock['add'] == add_r)
                    )
                if kondisi_kanan.any():
                    idx = kondisi_kanan.idxmax()
                    row_excel = idx + 2
                    stock_val = df_lensa_stock.at[idx, 'stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    stock_baru = max(0, stock_lama - 1)
                    try:
                        col_stock = worksheet_lensa_stock.find("Stock").col
                        worksheet_lensa_stock.update_cell(row_excel, col_stock, stock_baru)
                        df_lensa_stock.at[idx, 'stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock lensa kanan: {e}")
            # Update stok lensa kiri
            if item['status_lensa'] == "Stock":
                if item['tipe_lensa'].lower() == 'single vision':
                    kondisi_kiri = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == format_2digit(item['sph_l'])) &
                        (df_lensa_stock['cyl'] == format_2digit(item['cyl_l']))
                    )
                else:
                    add_l = str(item['add_l']).strip() if item['add_l'] else ""
                    kondisi_kiri = (
                        (df_lensa_stock['jenis'] == item['jenis_lensa']) &
                        (df_lensa_stock['tipe'] == item['tipe_lensa']) &
                        (df_lensa_stock['merk'] == item['merk_lensa']) &
                        (df_lensa_stock['sph'] == format_2digit(item['sph_l'])) &
                        (df_lensa_stock['cyl'] == format_2digit(item['cyl_l'])) &
                        (df_lensa_stock['add'] == add_l)
                    )
                if kondisi_kiri.any():
                    idx = kondisi_kiri.idxmax()
                    row_excel = idx + 2
                    stock_val = df_lensa_stock.at[idx, 'stock']
                    try:
                        stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                    except Exception:
                        stock_lama = 0
                    stock_baru = max(0, stock_lama - 1)
                    try:
                        col_stock = worksheet_lensa_stock.find("Stock").col
                        worksheet_lensa_stock.update_cell(row_excel, col_stock, stock_baru)
                        df_lensa_stock.at[idx, 'stock'] = stock_baru
                    except Exception as e:
                        st.warning(f"Gagal update stock lensa kiri: {e}")
 
         # Simpan pembayaran
        @st.cache_data(ttl=300)
        def load_pembayaran():
            return get_dataframe(SHEET_KEY, SHEET_NAMES['pembayaran_luar_kota'])

        df_pembayaran = load_pembayaran()
        pembayaran_ke = df_pembayaran[df_pembayaran['Id Transaksi'] == id_transaksi].shape[0] + 1

        pembayaran_data = [
            today, tanggal_ambil, id_transaksi, id_pembayaran, nama, metode, via,
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

    def reset_form_kasir():
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
                reset_form_kasir()
                st.rerun()
