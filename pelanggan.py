import streamlit as st
import pandas as pd
from utils import get_table_cached


def run():
    st.title("Database Pelanggan")

    # ==============================
    # Ambil Data dari Supabase
    # ==============================
    df_transaksi = get_table_cached("transaksi_detail")
    df_pelanggan = get_table_cached("pelanggan")

    if df_transaksi.empty or df_pelanggan.empty:
        st.warning("Data belum tersedia.")
        return

    # Merge pelanggan
    df = df_transaksi.merge(
        df_pelanggan[["id_pelanggan", "no_hp"]],
        on="id_pelanggan",
        how="left"
    )

    # Pastikan tanggal datetime
    df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")

    lens_cols = [
        "sph_r", "cyl_r", "axis_r", "add_r",
        "sph_l", "cyl_l", "axis_l", "add_l"
    ]

    # Bersihkan NaN
    for col in lens_cols:
        df[col] = df[col].astype(str).fillna("")

    results = []

    # ==============================
    # Proses Grouping Ukuran
    # ==============================
    for cust_id, group in df.groupby("id_pelanggan"):

        group = group.dropna(subset=["tanggal"])
        if group.empty:
            continue

        ukuran_group = group.groupby(lens_cols)

        for _, transaksi_group in ukuran_group:

            if transaksi_group.empty:
                continue

            last_row = transaksi_group.sort_values("tanggal").iloc[-1]

            def format_mata(sph, cyl, axis):
                if cyl in ["0", "0.0", "0.00", "", "None", None]:
                    return f"{sph}"
                return f"{sph} / {cyl} × {axis}"

            results.append({
                "ID Pelanggan": cust_id,
                "Nama": last_row["nama"],
                "No HP": last_row["no_hp"],
                "Mata R": format_mata(last_row["sph_r"], last_row["cyl_r"], last_row["axis_r"]),
                "Mata L": format_mata(last_row["sph_l"], last_row["cyl_l"], last_row["axis_l"]),
                "ADD": last_row["add_r"],
                "Tanggal Terakhir": last_row["tanggal"]
            })

    if not results:
        st.warning("Belum ada data ukuran.")
        return

    df_final = pd.DataFrame(results)

    # Urutkan terbaru dulu
    df_final = df_final.sort_values("ID Pelanggan", ascending=True)

    # ==============================
    # 🔎 SEARCH SECTION (No Enter Needed)
    # ==============================

    search = st.text_input(
        "Cari Nama atau No HP",
        placeholder="Ketik untuk mencari..."
    )

    if st.button("Reset"):
        search = ""

    if search:
        df_final = df_final[
            df_final["Nama"].str.contains(search, case=False, na=False) |
            df_final["No HP"].str.contains(search, case=False, na=False)
        ]

    # ==============================
    # Format Index
    # ==============================
    df_final = df_final.reset_index(drop=True)
    df_final.index = df_final.index + 1
    df_final.index.name = "No"

    st.dataframe(df_final, use_container_width=True)