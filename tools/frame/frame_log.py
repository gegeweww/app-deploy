import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

from utils import get_supabase


# ==========================================
# FUNGSI DASAR INSERT LOG
# ==========================================

def _insert_log(
    merk,
    kode,
    status,
    keterangan,
    user="Unknown"
):
    supabase = get_supabase()

    timestamp = datetime.now(
        ZoneInfo("Asia/Jakarta")
    )

    timestamp_str = timestamp.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    supabase.table("log_frames").insert({
        "timestamp_log": timestamp_str,
        "merk": merk,
        "kode": kode,
        "status": status,
        "keterangan": keterangan,
        "user_name": user
    }).execute()


# ==========================================
# LOG FRAME BARU
# ==========================================

def log_frame_baru(
    merk,
    kode,
    stock,
    user="Unknown"
):
    keterangan = (
        f"Frame Baru: "
        f"Merk: {merk}, "
        f"Kode: {kode}, "
        f"Jumlah: {stock}"
    )

    _insert_log(
        merk=merk,
        kode=kode,
        status="masuk",
        keterangan=keterangan,
        user=user
    )


# ==========================================
# LOG STOCK MASUK
# ==========================================

def log_frame_stock(
    merk,
    kode,
    jumlah_input,
    stock_lama,
    stock_baru,
    user="Unknown"
):
    keterangan = (
        f"Tambah Stock sebanyak {jumlah_input}, "
        f"stock lama: {stock_lama}, "
        f"stock baru: {stock_baru}"
    )

    _insert_log(
        merk=merk,
        kode=kode,
        status="masuk",
        keterangan=keterangan,
        user=user
    )


# ==========================================
# LOG PERUBAHAN DISTRIBUTOR
# ==========================================

def log_frame_distributor(
    merk,
    kode,
    distributor_lama,
    distributor_baru,
    user="Unknown"
):
    distributor_lama = (
        "NULL"
        if pd.isna(distributor_lama)
        else str(distributor_lama)
    )

    distributor_baru = (
        "NULL"
        if pd.isna(distributor_baru)
        else str(distributor_baru)
    )

    keterangan = (
        f"Revisi distributor: "
        f"{distributor_lama} → {distributor_baru}"
    )

    _insert_log(
        merk=merk,
        kode=kode,
        status="revisi",
        keterangan=keterangan,
        user=user
    )


# ==========================================
# LOG PERUBAHAN HARGA JUAL
# ==========================================

def log_frame_harga(
    merk,
    kode,
    harga_lama,
    harga_baru,
    user="Unknown"
):
    keterangan = (
        f"Revisi harga jual: "
        f"{harga_lama} → {harga_baru}"
    )

    _insert_log(
        merk=merk,
        kode=kode,
        status="revisi",
        keterangan=keterangan,
        user=user
    )


# ==========================================
# LOG FRAME TERJUAL
# ==========================================

def log_frame_terjual(
    merk,
    kode,
    id_transaksi,
    nama,
    user="Unknown"
):
    keterangan = (
        f"terjual dalam transaksi: "
        f"{id_transaksi}, Nama: {nama}"
    )

    _insert_log(
        merk=merk,
        kode=kode,
        status="terjual",
        keterangan=keterangan,
        user=user
    )