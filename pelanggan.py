import streamlit as st
import pandas as pd
from utils import get_dataframe
from constants import SHEET_KEY, SHEET_NAMES

def run():
    @st.cache_data(ttl=300)
    def show_data():
        data_transaksi = get_dataframe(SHEET_KEY, SHEET_NAMES['transaksi'])
        data_pelanggan = get_dataframe(SHEET_KEY, SHEET_NAMES['pelanggan'])
    
        return data_transaksi, data_pelanggan
    data_transaksi, data_pelanggan = show_data()    
    
    st.title("Database Pelanggan")
    # 🔎 filter otomatis
    nama = st.text_input("Cari Nama Pelanggan")
    
    data_transaksi = data_transaksi.merge(
        data_pelanggan[["ID Pelanggan", "No HP"]],
        on="ID Pelanggan",
        how="left"
    )
    
    lens_cols = ["SPH R", "CYL R", "Axis R", "Add R",
                 "SPH L", "CYL L", "Axis L", "Add L"]
    
    results = []
    # Group berdasarkan ID Pelanggan
    for cust_id, group in data_transaksi.groupby("ID Pelanggan"):
        # ambil data unik hanya berdasarkan ukuran
        unique_sizes = group[lens_cols].drop_duplicates()

        for _, ukuran in unique_sizes.iterrows():
            # filter transaksi dengan ukuran ini
            mask = group[lens_cols].eq(ukuran).all(axis=1)
            transaksi_match = group[mask]

            # ambil transaksi terakhir
            last_row = transaksi_match.sort_values("Tanggal").iloc[-1]
            
            def format_mata(sph, cyl, axis):
                # kalau cyl == "0.00" atau "0" → ga ditampilin
                if str(cyl) in ["0.00", "0", "0.0"]:
                    return f"{sph}"
                return f"{sph} / {cyl} × {axis}"
            
            data_transaksi["Mata R"] = data_transaksi.apply(lambda x: format_mata(x["SPH R"], x["CYL R"], x["Axis R"]), axis=1)
            data_transaksi["Mata L"] = data_transaksi.apply(lambda x: format_mata(x["SPH L"], x["CYL L"], x["Axis L"]), axis=1)

            results.append({
                "ID Pelanggan": cust_id,
                "Nama": last_row["Nama"],
                "No HP": last_row["No HP"],
                "Mata R": format_mata(last_row["SPH R"], last_row["CYL R"], last_row["Axis R"]),
                "Mata L": format_mata(last_row["SPH L"], last_row["CYL L"], last_row["Axis L"]),
                "ADD": ukuran["Add R"],
                "Tanggal Terakhir": last_row["Tanggal"]
            })
            
    df_pelanggan = pd.DataFrame(results).reset_index(drop=True)
    df_pelanggan.index = df_pelanggan.index + 1
    df_pelanggan.index.name = "No"
    
    if nama:  # kalau ada input
        df_filtered = df_pelanggan[df_pelanggan["Nama"].str.contains(nama, case=False, na=False)]
        st.dataframe(df_filtered)
    else:  # kalau kosong → tampilkan semua
        st.dataframe(df_pelanggan)