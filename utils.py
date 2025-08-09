import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from constants import SHEET_NAMES
import streamlit as st
from zoneinfo import ZoneInfo

# Font
def set_font():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');

        html, body, div, span, input, textarea, select, label, button, p, h1, h2, h3, h4, h5, h6 {
            font-family: 'Roboto', sans-serif !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Autentikasi dan akses Google Sheet
def authorize_gspread():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], # type: ignore
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    return client
def get_sheet(sheet_key: str, sheet_name: str):
    client = authorize_gspread()
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    return sheet

# Baca isi sheet ke DataFrame dan bersihkan
def get_dataframe(sheet_key: str, sheet_name: str):
    sheet = get_sheet(sheet_key, sheet_name)
    values = sheet.get_all_values()

    if not values or not values[0]:
        raise ValueError(f"Sheet '{sheet_name}' kosong atau tidak memiliki header.")

    headers = values[0]
    data = values[1:]

    df = pd.DataFrame(data, columns=headers)

    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.strip()
        except:
            df[col] = df[col].astype(str)

    return df


# Tambahkan satu baris ke sheet
def append_row(sheet_key, sheet_name, data_row):
    client = authorize_gspread()
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    sheet.append_row(data_row)

# Tambahkan beberapa baris ke sheet
def append_rows(sheet_key, sheet_name, data_rows):
    client = authorize_gspread()
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    sheet.append_rows(data_rows, value_input_option="USER_ENTERED")

# Sort Data Frame (A-Z)
def sort_sheet(sheet, col=1, last_col='F'):
    values = sheet.get_all_values()
    total_rows = len(values)
    sheet.sort((col, 'asc'), range=f"A2:{last_col}{total_rows}")

# Buat atau cek id pelanggan
def get_or_create_pelanggan_id(sheet_key, sheet_name, nama, no_hp):
    df = get_dataframe(sheet_key, sheet_name)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Cek apakah sudah ada
    existing = df[(df['nama'] == nama) & (df['no_hp'] == no_hp)]
    if not existing.empty:
        return existing.iloc[0]['id_pelanggan']

    # Generate ID baru
    id_baru = f"OM{len(df)+1:03}"
    new_row = [id_baru, nama, no_hp]
    append_row(sheet_key, sheet_name, new_row)
    return id_baru


# Buat id transaksi
def generate_id_transaksi(sheet_key, sheet_name, tanggal_transaksi):
    df = get_dataframe(sheet_key, sheet_name)
    df.columns = df.columns.str.strip()

    urutan = 1
    if not df.empty and 'ID Transaksi' in df.columns:
        existing_ids = df['ID Transaksi'].dropna().tolist()
        nomor_list = []
        for tid in existing_ids:
            try:
                nomor = int(tid.split("/")[2])
                nomor_list.append(nomor)
            except:
                continue
        if nomor_list:
            urutan = max(nomor_list) + 1

    # Format: DD-MM/YYYY
    hari_bulan = tanggal_transaksi.strftime("%d-%m")
    tahun = tanggal_transaksi.strftime("%Y")
    id_transaksi = f"OM/T/{urutan:03d}/{hari_bulan}/{tahun}"
    return id_transaksi

# Buat id transaksi pesanan luar kota
def generate_id_skw(sheet_key, sheet_name, nama, tanggal_ambil):
    df = get_dataframe(sheet_key, sheet_name)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    kode = "01" if nama == "Nelly" else "02"
    tanggal_str = pd.to_datetime(tanggal_ambil).strftime("%d-%m-%Y")

    # Ambil semua id_transaksi yang valid (tidak perlu filter tanggal)
    if 'id_transaksi' not in df.columns:
        next_num = 1
    else:
        df = df[df['id_transaksi'].str.contains(r"OMSKW/\d+/\d+/")]
        if df.empty:
            next_num = 1
        else:
            df['urutan'] = df['id_transaksi'].str.extract(r"OMSKW/\d+/(\d+)/")[0].astype(int)
            next_num = df['urutan'].max() + 1

    return f"OMSKW/{kode}/{next_num:03}/{tanggal_str}"



# Buat id pembayaran
def generate_id_pembayaran(sheet_key, sheet_name, tanggal_pembayaran):
    df = get_dataframe(sheet_key, sheet_name)
    df.columns = df.columns.str.strip()

    urutan = 1
    if 'ID Pembayaran' in df.columns:
        existing_ids = df['ID Pembayaran'].dropna().tolist()
        nomor_list = []
        for pid in existing_ids:
            try:
               if pid.startswith("OM/P/"):
                   n = int(pid.split("/")[2])
                   nomor_list.append(n)
            except:
                continue
        if nomor_list:
            urutan = max(nomor_list) + 1

    # Format: DD-MM/YYYY
    hari_bulanp = tanggal_pembayaran.strftime("%d-%m")
    tahunp = tanggal_pembayaran.strftime("%Y")
    id_pembayaran = f"OM/P/{urutan:03d}/{hari_bulanp}/{tahunp}"
    return id_pembayaran

# Buat id pembayaran pesanan luar kota
def generate_id_pemb_skw(sheet_key, sheet_name, nama, tanggal_ambil):
    df = get_dataframe(sheet_key, sheet_name)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    kode = "01" if nama == "Nelly" else "02"
    tanggal_str = pd.to_datetime(tanggal_ambil).strftime("%d-%m-%Y")

    # Ambil semua id_pembayaran yang valid (tidak perlu filter tanggal)
    if 'id_pembayaran' not in df.columns:
        next_num = 1
    else:
        df = df[df['id_pembayaran'].str.contains(r"OMSKW/P/\d+/\d+/")]
        if df.empty:
            next_num = 1
        else:
            df['urutan'] = df['id_pembayaran'].str.extract(r"OMSKW/P/\d+/(\d+)/")[0].astype(int)
            next_num = df['urutan'].max() + 1

    return f"OMSKW/P/{kode}/{next_num:03}/{tanggal_str}"

# Cari Harga Lensa Stock
def cari_harga_lensa_stock(df_stock, tipe, jenis, merk, sph, cyl, add, pakai_reseller=True):
    df_stock.columns = df_stock.columns.str.lower().str.strip().str.replace(" ", "_")
    kolom_harga = 'harga_reseller' if pakai_reseller else 'harga_jual'

    try:
        harga = df_stock[
            (df_stock['tipe'].str.lower() == tipe.lower()) &
            (df_stock['jenis'].str.lower() == jenis.lower()) &
            (df_stock['merk'].str.lower() == merk.lower()) &
            (df_stock['sph'].str.lower() == sph.lower()) &
            (df_stock['cyl'].str.lower() == cyl.lower()) & 
            (df_stock['add'].str.lower() == add.lower())
        ][kolom_harga]\
        .astype(str)\
        .str.replace("rp", "", case=False)\
        .str.replace(".", "")\
        .str.replace(",", "")\
        .str.strip()\
        .astype(int)\
        .values[0]
        return harga
    except:
        return None

# Cari Harga Lensa Luar Stock
def cari_harga_lensa_luar(df, tipe, nama_lensa, sph, cyl, add, pakai_reseller=True):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    tipe = (tipe or "").strip().lower()
    jenis = (jenis or "").strip().lower()
    nama_lensa = (nama_lensa or "").strip().lower()
    kolom_harga = 'harga_reseller' if pakai_reseller else 'harga_jual'

    try:
        sph = float(str(sph).replace(",", "."))
        cyl = float(str(cyl).replace(",", "."))
        add = float(str(add).replace(",", ".")) if add not in ["", None] else None

    except ValueError:
        return None
    
    df_filtered = df[
        (df['tipe'].str.lower() == tipe) &
        (df['jenis'].str.lower() == jenis) &
        (df['nama_lensa'].str.lower() == nama_lensa)
    ].copy()

    # Tambahkan kolom prioritas: 2 = CYL & ADD cocok, 1 = CYL cocok, 0 = umum
    def calculate_priority(row):
        has_cyl = pd.notna(pd.to_numeric(row.get("cyl_min"), errors="coerce")) and pd.notna(pd.to_numeric(row.get("cyl_max"), errors="coerce"))
        has_add = pd.notna(pd.to_numeric(row.get("add_min"), errors="coerce")) and pd.notna(pd.to_numeric(row.get("add_max"), errors="coerce"))
        return int(has_cyl) + int(has_add)

    df_filtered["prioritas"] = df_filtered.apply(calculate_priority, axis=1)
    df_filtered = df_filtered.sort_values("prioritas", ascending=False)

    for _, row in df_filtered.iterrows():
        try:
            sph_min = float(row['sph_min'])
            sph_max = float(row['sph_max'])
        except (ValueError, TypeError):
            continue

        if not (sph_min <= sph <= sph_max):
            continue

        cyl_min = pd.to_numeric(row.get('cyl_min'), errors='coerce')
        cyl_max = pd.to_numeric(row.get('cyl_max'), errors='coerce')
        if pd.notna(cyl_min) and pd.notna(cyl_max):
            if not (cyl_min <= cyl <= cyl_max):
                continue

        add_min = pd.to_numeric(row.get('add_min'), errors='coerce')
        add_max = pd.to_numeric(row.get('add_max'), errors='coerce')
        if add is not None and pd.notna(add_min) and pd.notna(add_max):
            if not (add_min <= add <= add_max):
                continue

        kolom_harga = 'harga_reseller' if pakai_reseller else 'harga_jual'
        harga_str = str(row.get(kolom_harga, "")).replace("Rp", "").replace(".", "").replace(",", "").strip()

        try:
            return int(harga_str)
        except ValueError:
            continue

    return None


# Buat status log untuk frame
def buat_logframe_status(source: str, mode=None, status_frame=None, merk=None, kode=None, jumlah_input=None, stock_lama=None, stock_baru=None, id_transaksi=None, nama=None):
    if source == 'iframe':
        if mode == 'Tambah Stock':
            return 'masuk', f'Tambah Stock sebanyak {jumlah_input}, stock lama: {stock_lama}, stock baru: {stock_baru}'
        elif mode == 'Tambah Merk':
            return 'masuk', f'Merk Baru: {merk}, Kode Baru: {kode}, Jumlah: {stock_baru}'
        elif mode == 'Tambah Kode':
            return 'masuk', f'Merk: {merk}, Kode Baru: {kode}, Jumlah: {stock_baru}'
        elif mode == 'Revisi':
            return 'revisi', f'ubah dari {stock_lama} jadi {stock_baru}'
    elif source == 'kasir':
        if status_frame == 'Stock':
            return 'terjual', f'terjual dalam transaksi: {id_transaksi}, Nama: {nama}'
        else:
            return '', ''

def buat_loglensa_status(source: str, mode=None, status_lensa=None, jenis=None, tipe=None, merk=None, sph=None, cyl=None, add=None, stock_lama=None, stock_baru=None, id_transaksi=None, nama=None, jumlah_input=None):
    if source == 'ilensa':
        return 'masuk', f'Tambah stock sebanyak {jumlah_input}, stock lama: {stock_lama}, stock baru: {stock_baru}'
    elif source == 'kasir':
        if status_lensa == 'Stock':
            return 'terjual', f'terjual dalam transaksi: {id_transaksi}, Nama: {nama}'
    elif source == 'luarkota':
        if status_lensa == 'Stock':
            return 'terjual', f'terjual dalam transaksi: {id_transaksi}, Nama: {nama}'
        
def catat_logframe(sheet_key, sheet_name, merk, kode, source, mode=None, status_frame=None, jumlah_input=None, stock_lama=None, stock_baru=None, id_transaksi=None, nama=None, user="Unknown"):
    from datetime import datetime, timedelta
    import pandas as pd

    status_log, keterangan = buat_logframe_status(
        source=source,
        mode=mode,
        status_frame=status_frame,
        merk=merk,
        kode=kode,
        jumlah_input=jumlah_input,
        stock_lama=stock_lama,
        stock_baru=stock_baru,
        id_transaksi=id_transaksi,
        nama=nama
    )
    
    if status_log and keterangan:
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta"))
        timestamp_str = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        
        # Check if the same log entry already exists
        try:
            df_log = get_dataframe(sheet_key, sheet_name)
            
            # For sales transactions, check for the same transaction ID
            if source == 'kasir' and id_transaksi:
                mask = (
                    (df_log['Keterangan'].str.contains(id_transaksi, na=False)) &
                    (df_log['Merk'] == merk) &
                    (df_log['Kode'] == kode)
                )
            # For stock updates, check for similar entries in the last 5 minutes
            elif source == 'iframe':
                five_min_ago = (timestamp - timedelta(minutes=5)).strftime("%d-%m-%Y %H:%M:%S")
                mask = (
                    (df_log['Merk'] == merk) & 
                    (df_log['Kode'] == kode) & 
                    (df_log['Status'] == status_log) &
                    (df_log['Keterangan'] == keterangan) &
                    (df_log['Timestamp'] >= five_min_ago)
                )
            else:
                mask = pd.Series(False)  # No match if not kasir or iframe
            
            # If no duplicate found, add the new log entry
            if not mask.any():
                row = [timestamp_str, merk, kode, status_log, keterangan, user]
                append_row(sheet_key, sheet_name, row)
                
        except Exception as e:
            # If there's any error (e.g., sheet empty), just add the log entry
            row = [timestamp_str, merk, kode, status_log, keterangan, user]
            append_row(sheet_key, sheet_name, row)


def catat_loglensa(sheet_key, sheet_name, jenis, tipe, merk, sph, cyl, add, source, mode=None, status_lensa=None, jumlah_input=None, stock_lama=None, stock_baru=None, id_transaksi=None, nama=None, user="Unknown"):
    from datetime import datetime, timedelta

    status_log, keterangan = buat_loglensa_status(
        source=source,
        status_lensa=status_lensa,
        jenis=jenis,
        tipe=tipe,
        merk=merk,
        sph=sph,
        cyl=cyl,
        add=add,
        jumlah_input=jumlah_input,
        stock_lama=stock_lama,
        stock_baru=stock_baru,
        id_transaksi=id_transaksi,
        nama=nama
    )
    
    if status_log and keterangan:
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta"))
        timestamp_str = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        
        # Check if the same log entry already exists
        try:
            df_log = get_dataframe(sheet_key, sheet_name)
            
            # For sales transactions, check for the same transaction ID
            if source in ['kasir', 'luarkota'] and id_transaksi:
                mask = (
                    (df_log['Keterangan'].str.contains(id_transaksi, na=False)) &
                    (df_log['Merk'] == merk) &
                    (df_log['Jenis'] == jenis) &
                    (df_log['Tipe'] == tipe) &
                    (df_log['SPH'] == str(sph)) &
                    (df_log['CYL'] == str(cyl)) &
                    (df_log['Add'] == str(add))
                )
            # For stock updates, check for similar entries in the last 5 minutes
            elif source == 'ilensa':
                five_min_ago = (timestamp - timedelta(minutes=5)).strftime("%d-%m-%Y %H:%M:%S")
                mask = (
                    (df_log['Merk'] == merk) & 
                    (df_log['Jenis'] == jenis) & 
                    (df_log['Tipe'] == tipe) & 
                    (df_log['SPH'] == str(sph)) & 
                    (df_log['CYL'] == str(cyl)) & 
                    (df_log['Add'] == str(add)) &
                    (df_log['Status'] == status_log) &
                    (df_log['Keterangan'] == keterangan) &
                    (df_log['Timestamp'] >= five_min_ago)
                )
            else:
                mask = pd.Series(False)  # No match if source not recognized
            
            # If no duplicate found, add the new log entry
            if not mask.any():
                row = [timestamp_str, tipe, merk, jenis, sph, cyl, add, status_log, keterangan, user]
                append_row(sheet_key, sheet_name, row)
                
        except Exception as e:
            # If there's any error (e.g., sheet empty), just add the log entry
            row = [timestamp_str, tipe, merk, jenis, sph, cyl, add, status_log, keterangan, user]
            append_row(sheet_key, sheet_name, row)
