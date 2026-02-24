import gspread
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from google.oauth2.service_account import Credentials
from constants import SHEET_NAMES
import streamlit as st
from zoneinfo import ZoneInfo
from supabase import create_client

@st.cache_resource
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

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

# Baca isi database
def get_dataframe_supabase(table_name):
    supabase = get_supabase()
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

def get_table_raw(table_name):
    supabase = get_supabase()
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=60)
def get_table_cached(table_name):
    return get_table_raw(table_name)

# Tambahkan satu baris ke sheet
def append_row(sheet_key, sheet_name, data_row):
    client = authorize_gspread()
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    sheet.append_row(data_row)
  
# Tambahkan satu baris ke tabel supabase  
def insert_row_supabase(table_name, data_dict):
    supabase = get_supabase()
    clean_data = {}
    for key, value in data_dict.items():
        # ✅ Convert date & datetime
        if isinstance(value, (date, datetime)):
            clean_data[key] = value.isoformat()
        # ✅ Convert pandas timestamp
        elif isinstance(value, (pd.Timestamp, np.datetime64)):
            clean_data[key] = str(value)
        # ✅ Convert numpy numbers
        elif isinstance(value, (np.integer, np.int64)):
            clean_data[key] = int(value)
        elif isinstance(value, (np.floating,)):
            clean_data[key] = float(value)
        elif value == "":
            clean_data[key] = None
        else:
            clean_data[key] = value
    response = supabase.table(table_name).insert(clean_data).execute()
    return response

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

def get_or_create_pelanggan_id_supabase(nama, no_hp):
    supabase = get_supabase()

    # ==============================
    # Normalisasi input
    # ==============================
    nama_clean = str(nama).strip().lower()
    no_hp_clean = str(no_hp).strip()

    if not nama_clean:
        raise ValueError("Nama tidak boleh kosong")

    if not no_hp_clean:
        raise ValueError("No HP tidak boleh kosong")

    # ==============================
    # 1️⃣ Cek EXACT MATCH nama + no_hp
    # ==============================
    existing = supabase.table("pelanggan") \
        .select("id_pelanggan") \
        .eq("nama", nama_clean) \
        .eq("no_hp", no_hp_clean) \
        .execute()

    if existing.data:
        return existing.data[0]["id_pelanggan"]

    # ==============================
    # 2️⃣ Generate ID baru
    # ==============================
    response_all = supabase.table("pelanggan") \
        .select("id_pelanggan") \
        .execute()

    existing_ids = [
        row["id_pelanggan"]
        for row in response_all.data
        if row.get("id_pelanggan", "").startswith("OM")
    ]

    nomor_list = []
    for pid in existing_ids:
        try:
            nomor = int(pid.replace("OM", ""))
            nomor_list.append(nomor)
        except:
            continue

    urutan = max(nomor_list) + 1 if nomor_list else 1
    id_baru = f"OM{urutan:03d}"

    # ==============================
    # 3️⃣ Insert pelanggan baru
    # ==============================
    insert_result = supabase.table("pelanggan").insert({
        "id_pelanggan": id_baru,
        "nama": nama_clean,
        "no_hp": no_hp_clean
    }).execute()

    if insert_result.data:
        return id_baru
    else:
        raise Exception("Gagal insert pelanggan ke Supabase")
    
# Buat id transaksi
def generate_id_transaksi_supabase(tanggal_transaksi):
    supabase = get_supabase()

    # Ambil semua id_transaksi
    response = supabase.table("transaksi") \
        .select("id_transaksi") \
        .execute()

    existing_ids = [row["id_transaksi"] for row in response.data if row.get("id_transaksi")]

    nomor_list = []

    for tid in existing_ids:
        try:
            # Format: OM/T/001/10-05/2025
            nomor = int(tid.split("/")[2])
            nomor_list.append(nomor)
        except:
            continue

    urutan = max(nomor_list) + 1 if nomor_list else 1

    hari_bulan = tanggal_transaksi.strftime("%d-%m")
    tahun = tanggal_transaksi.strftime("%Y")

    return f"OM/T/{urutan:03d}/{hari_bulan}/{tahun}"

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
def generate_id_pembayaran_supabase(tanggal_pembayaran):
    supabase = get_supabase()

    response = supabase.table("pembayaran") \
        .select("id_pembayaran") \
        .execute()

    existing_ids = [row["id_pembayaran"] for row in response.data if row.get("id_pembayaran")]

    nomor_list = []

    for pid in existing_ids:
        try:
            # Format: OM/P/001/10-05/2025
            if pid.startswith("OM/P/"):
                nomor = int(pid.split("/")[2])
                nomor_list.append(nomor)
        except:
            continue

    urutan = max(nomor_list) + 1 if nomor_list else 1

    hari_bulan = tanggal_pembayaran.strftime("%d-%m")
    tahun = tanggal_pembayaran.strftime("%Y")

    return f"OM/P/{urutan:03d}/{hari_bulan}/{tahun}"

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
            (df_stock['add_power'].str.lower() == add.lower())
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
def cari_harga_lensa_luar(df, tipe, jenis, nama_lensa, sph, cyl, add, pakai_reseller=True):
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

        add_min = pd.to_numeric(row.get('add_min_power'), errors='coerce')
        add_max = pd.to_numeric(row.get('add_max_power'), errors='coerce')
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

# Versi supabase
def catat_logframe_supabase(
    merk,
    kode,
    source,
    mode=None,
    status_frame=None,
    jumlah_input=None,
    stock_lama=None,
    stock_baru=None,
    id_transaksi=None,
    nama=None,
    user="Unknown"
):
    """
    Versi Supabase dari catat_logframe (mengikuti logika lama)
    """

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

    if not status_log or not keterangan:
        return

    supabase = get_supabase()

    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # ==============================
    # CEK DUPLICATE FRAME LOG DI SUPABASE
    # ==============================

    response = supabase.table("log_frames") \
        .select("*") \
        .eq("merk", merk) \
        .eq("kode", kode) \
        .execute()

    df_log = pd.DataFrame(response.data)

    duplicate = False

    if not df_log.empty:
        if source == "kasir" and id_transaksi:
            duplicate = df_log["keterangan"].str.contains(
                id_transaksi, na=False
            ).any()

    # ==============================
    # INSERT JIKA TIDAK DUPLICATE
    # ==============================

    if not duplicate:
        supabase.table("log_frames").insert({
            "timestamp_log": timestamp_str,
            "merk": merk,
            "kode": kode,
            "status": status_log,
            "keterangan": keterangan,
            "user_name": user
        }).execute()

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
            
# Versi loglensa Supabase
def buat_loglensa_status(
    source: str,
    mode=None,
    status_lensa=None,
    jenis=None,
    tipe=None,
    merk=None,
    sph=None,
    cyl=None,
    add=None,
    stock_lama=None,
    stock_baru=None,
    id_transaksi=None,
    nama=None,
    jumlah_input=None
):
    if source == "ilensa":
        return "masuk", f"Tambah stock sebanyak {jumlah_input}, stock lama: {stock_lama}, stock baru: {stock_baru}"

    elif source in ["kasir", "luarkota"]:
        if status_lensa == "Stock":
            return "terjual", f"Terjual dalam transaksi: {id_transaksi}, Nama: {nama}"

    return None, None

def catat_loglensa_supabase(
    jenis,
    tipe,
    merk,
    sph,
    cyl,
    add_power,
    source,
    mode=None,
    status_lensa=None,
    jumlah_input=None,
    stock_lama=None,
    stock_baru=None,
    id_transaksi=None,
    nama=None,
    user="Unknown"
):

    status_log, keterangan = buat_loglensa_status(
        source=source,
        mode=mode,
        status_lensa=status_lensa,
        jenis=jenis,
        tipe=tipe,
        merk=merk,
        sph=sph,
        cyl=cyl,
        add=add_power,
        jumlah_input=jumlah_input,
        stock_lama=stock_lama,
        stock_baru=stock_baru,
        id_transaksi=id_transaksi,
        nama=nama
    )

    if not status_log or not keterangan:
        return

    supabase = get_supabase()
    timestamp = datetime.now()
    five_min_ago = timestamp - timedelta(minutes=5)

    # ==============================
    # CEK DUPLICATE
    # ==============================

    response = supabase.table("log_lensa") \
        .select("*") \
        .eq("merk", merk) \
        .eq("jenis", jenis) \
        .eq("tipe", tipe) \
        .eq("sph", str(sph)) \
        .eq("cyl", str(cyl)) \
        .eq("add_power", str(add_power)) \
        .execute()

    df_log = pd.DataFrame(response.data)
    duplicate = False

    if not df_log.empty:

        # Duplicate untuk kasir / luarkota
        if source in ["kasir", "luarkota"] and id_transaksi:
            duplicate = df_log["keterangan"].str.contains(
                id_transaksi, na=False
            ).any()

        # Duplicate untuk ilensa (5 menit)
        elif source == "ilensa":

            df_log["timestamp_log"] = pd.to_datetime(
                df_log["timestamp_log"], errors="coerce"
            )

            mask = (
                (df_log["status"] == status_log) &
                (df_log["keterangan"] == keterangan) &
                (df_log["timestamp_log"] >= five_min_ago)
            )

            duplicate = mask.any()

    # ==============================
    # INSERT JIKA TIDAK DUPLICATE
    # ==============================

    if not duplicate:
        supabase.table("log_lensa").insert({
            "timestamp_log": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "tipe": tipe,
            "merk": merk,
            "jenis": jenis,
            "sph": str(sph),
            "cyl": str(cyl),
            "add_power": str(add_power),
            "status": status_log,
            "keterangan": keterangan,
            "user_name": user
        }).execute()