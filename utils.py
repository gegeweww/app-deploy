import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import streamlit as st

# Autentikasi dan akses Google Sheet
def get_gsheet_client(json_path):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)
    return client

def authorize_gspread(json_path):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(json_path, scopes=scopes)
    client = gspread.authorize(credentials)
    return client

def get_sheet(sheet_key: str, json_path: str, sheet_name: str):
    client = get_gsheet_client(json_path)
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    return sheet

# Baca isi sheet ke DataFrame dan bersihkan
def get_dataframe(sheet_key: str, json_path: str, sheet_name: str):
    sheet = get_sheet(sheet_key, json_path, sheet_name)
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
def append_row(sheet_key, json_path, sheet_name, row_data):
    client = authorize_gspread(json_path)
    sheet = client.open_by_key(sheet_key).worksheet(sheet_name)
    sheet.append_row(row_data)

# Buat atau cek id pelanggan
def get_or_create_pelanggan_id(sheet_key, json_path, sheet_name, nama, no_hp):
    df = get_dataframe(sheet_key, json_path, sheet_name)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Cek apakah sudah ada
    existing = df[(df['nama'] == nama) & (df['no_hp'] == no_hp)]
    if not existing.empty:
        return existing.iloc[0]['id_pelanggan']

    # Generate ID baru
    id_baru = f"OM{len(df)+1:03}"
    new_row = [id_baru, nama, no_hp]
    append_row(sheet_key, json_path, sheet_name, new_row)
    return id_baru


# Buat id transaksi
def generate_id_transaksi(sheet_key, json_path, sheet_name, tanggal_transaksi):
    df = get_dataframe(sheet_key, json_path, sheet_name)
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

# Buat id pembayaran
def generate_id_pembayaran(sheet_key, json_path, sheet_name, tanggal_pembayaran):
    df = get_dataframe(sheet_key, json_path, sheet_name)
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

def cari_harga_lensa_luar(df_luar, nama_lensa, sph, cyl, add):
    try:
        sph = float(sph)
        cyl = float(cyl) if cyl not in ["", "-"] else None
        add = float(add) if add not in ["", "-"] else None
    except:
        return None  # Gagal parsing input

    df_cocok = df_luar[df_luar['nama_lensa'].str.lower() == nama_lensa.lower()]

    for _, row in df_cocok.iterrows():
        try:
            # Ambil rentang
            sph_min, sph_max = row['sph_min'], row['sph_max']
            cyl_min, cyl_max = row['cyl_min'], row['cyl_max']
            add_min, add_max = row['add_min'], row['add_max']

            # Validasi SPH
            if sph_min != "-" and sph_max != "-" and not (sph_min <= sph <= sph_max):
                continue
            # Validasi CYL
            if cyl_min != "-" and cyl_max != "-" and cyl is not None and not (cyl_min <= cyl <= cyl_max):
                continue
            # Validasi ADD
            if add_min != "-" and add_max != "-" and add is not None and not (add_min <= add <= add_max):
                continue

            return int(row['harga'])  # Cocok ketemu
        except:
            continue

    return None  # Tidak ditemukan

def cari_harga_lensa(df_lensa, nama_lensa, sph, cyl, add):
    """
    Cari harga dari sheet lensa stock (MLensa) berdasarkan nama lensa dan ukuran.

    Prioritas pencocokan: nama_lensa, sph, cyl, add (jika ada).
    """
    df = df_lensa.copy()
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    # Filter berdasarkan nama lensa dulu
    df = df[df['nama_lensa'].str.lower() == nama_lensa.lower()]

    # Filter SPH dan CYL
    df = df[(df['sph'] == sph) & (df['cyl'] == cyl)]

    # Jika ada kolom add, cocokkan juga
    if 'add' in df.columns and add:
        df = df[df['add'] == add]

    if not df.empty:
        try:
            return int(float(df.iloc[0]['harga']))
        except:
            return None
    return None
