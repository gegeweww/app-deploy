import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import streamlit as st
from zoneinfo import ZoneInfo
from supabase import create_client

@st.cache_resource
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_role_key"]
    return create_client(url, key)

# Font
def set_font():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&display=swap');

        html, body, div, span, input, textarea, select, label, button, p, h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Baca isi database
def get_dataframe_supabase(table_name):
    supabase = get_supabase()
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

def get_table_raw(table_name):
    supabase = get_supabase()
    all_data = []
    page = 0
    page_size = 1000

    while True:
        response = (
            supabase.table(table_name)
            .select("*")
            .range(page * page_size, (page + 1) * page_size - 1)
            .execute()
        )

        if not response.data:
            break

        all_data.extend(response.data)

        if len(response.data) < page_size:
            break

        page += 1

    df = pd.DataFrame(all_data)

    if not df.empty:
        df = df.replace([np.inf, -np.inf], np.nan)

        numeric_cols = ["harga_modal", "harga_jual", "stock"]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                ).fillna(0)

    return df

@st.cache_data(ttl=300)
def get_table_cached(table_name):
    try:
        df = get_table_raw(table_name)

        if df is None:
            return pd.DataFrame()

        return df

    except Exception as e:
        print(f"Error get_table_cached({table_name}): {e}")
        return pd.DataFrame()
  
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
def generate_id_skw_supabase(nama, tanggal_ambil):

    supabase = get_supabase()

    kode = "01" if nama == "Nelly" else "02"
    tanggal_str = pd.to_datetime(tanggal_ambil).strftime("%d-%m-%Y")

    # Ambil semua id_transaksi yang valid
    response = supabase.table("pesanan_luar_kota") \
        .select("id_transaksi") \
        .execute()

    data = response.data

    if not data:
        next_num = 1
    else:
        df = pd.DataFrame(data)

        df = df[df["id_transaksi"].str.contains(r"OMSKW/\d+/\d+/")]

        if df.empty:
            next_num = 1
        else:
            df["urutan"] = df["id_transaksi"] \
                .str.extract(r"OMSKW/\d+/(\d+)/")[0] \
                .astype(int)

            next_num = df["urutan"].max() + 1

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
def generate_id_pemb_skw_supabase(nama, tanggal_ambil):

    supabase = get_supabase()

    kode = "01" if nama == "Nelly" else "02"
    tanggal_str = pd.to_datetime(tanggal_ambil).strftime("%d-%m-%Y")

    response = supabase.table("pembayaran_luar_kota") \
        .select("id_pembayaran") \
        .execute()

    data = response.data

    if not data:
        next_num = 1
    else:
        df = pd.DataFrame(data)

        df = df[df["id_pembayaran"].str.contains(r"OMSKW/P/\d+/\d+/")]

        if df.empty:
            next_num = 1
        else:
            df["urutan"] = df["id_pembayaran"] \
                .str.extract(r"OMSKW/P/\d+/(\d+)/")[0] \
                .astype(int)

            next_num = df["urutan"].max() + 1

    return f"OMSKW/P/{kode}/{next_num:03}/{tanggal_str}"

# Cari harga lensa stock
def cari_harga_lensa_stock(df_stock, tipe, jenis, merk, sph, cyl, add, pakai_reseller=True):
    df = df_stock.copy()
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")
    kolom_harga = 'harga_reseller' if pakai_reseller else 'harga_jual'

    try:
        sph = round(float(sph), 2)
        cyl = round(float(cyl), 2)
        add = round(float(add), 2) if add is not None else None
    except:
        return None

    # Convert kolom ke numeric dulu
    df['sph'] = pd.to_numeric(df['sph'], errors='coerce')
    df['cyl'] = pd.to_numeric(df['cyl'], errors='coerce')
    df['add_power'] = pd.to_numeric(df['add_power'], errors='coerce')

    df_filtered = df[
        (df['tipe'].str.lower() == tipe.lower()) &
        (df['jenis'].str.lower() == jenis.lower()) &
        (df['merk'].str.lower() == merk.lower()) &
        (df['sph'].round(2) == sph) &
        (df['cyl'].round(2) == cyl)
    ]

    if add is not None:
        df_filtered = df_filtered[df_filtered['add_power'].round(2) == add]
    else:
        df_filtered = df_filtered[df_filtered['add_power'].isna()]

    if df_filtered.empty:
        return None

    return int(float(df_filtered.iloc[0][kolom_harga]))

# Cari Harga Lensa Luar Stock
def cari_harga_lensa_luar(df, tipe, jenis, nama_lensa, sph, cyl, add, pakai_reseller=True):
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()
    kolom_harga = "harga_reseller" if pakai_reseller else "harga_jual"

    try:
        sph = round(float(sph), 2)
        cyl = round(float(cyl), 2)
        add = round(float(add), 2) if add not in ["", None] else None
    except:
        return None

    # Filter awal
    df = df[
        (df["tipe"].str.lower() == tipe.lower()) &
        (df["jenis"].str.lower() == jenis.lower()) &
        (df["nama_lensa"].str.lower() == nama_lensa.lower())
    ]

    if df.empty:
        return None

    # =========================================
    # FILTER NUMERIC (NO LOOP 🔥)
    # =========================================

    query = (
        (df["sph_min"] <= sph) &
        (df["sph_max"] >= sph)
    )

    # CYL optional
    query &= (
        df["cyl_min"].isna() |
        ((df["cyl_min"] <= cyl) & (df["cyl_max"] >= cyl))
    )

    # ADD optional
    if add is not None:
        query &= (
            df["add_min_power"].isna() |
            ((df["add_min_power"] <= add) & (df["add_max_power"] >= add))
        )
    else:
        query &= df["add_min_power"].isna()

    df_filtered = df[query]

    if df_filtered.empty:
        return None

    # Ambil prioritas terbaik (opsional tapi bagus)
    df_filtered["prioritas"] = (
        df_filtered["cyl_min"].notna().astype(int) * 2 +
        df_filtered["add_min_power"].notna().astype(int)
    )

    df_filtered = df_filtered.sort_values("prioritas", ascending=False)

    return int(df_filtered.iloc[0][kolom_harga])

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

# Catat Log Frame
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

    timestamp = datetime.now(ZoneInfo("Asia/Jakarta"))
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
            
# Catat Log Lensa
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
    timestamp = datetime.now(ZoneInfo("Asia/Jakarta"))
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
            ).dt.tz_localize(None)  # strip timezone supaya bisa dibanding

            five_min_ago_naive = five_min_ago.replace(tzinfo=None)  # strip juga

            mask = (
                (df_log["status"] == status_log) &
                (df_log["keterangan"] == keterangan) &
                (df_log["timestamp_log"] >= five_min_ago_naive)
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