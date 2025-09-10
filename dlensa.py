import streamlit as st
import pandas as pd
from utils import get_dataframe
from constants import SHEET_KEY, SHEET_NAMES

def run():
    @st.cache_data(ttl=300)
    def show_data():
        df_lensa = get_dataframe(SHEET_KEY, SHEET_NAMES['dlensa'])
        df_lensa_cepat = get_dataframe(SHEET_KEY, SHEET_NAMES['lensacepat'])
        df_harga = get_dataframe(SHEET_KEY, SHEET_NAMES['hargalensa'])

        return df_lensa, df_lensa_cepat, df_harga

    st.title("Database Lensa")

    df_lensa, df_lensa_cepat, df_harga = show_data()
    
    st.header("Harga Lensa", divider="rainbow")
    st.dataframe(df_harga.reset_index(drop=True).to_dict("records"), use_container_width=True)


    def display_df_with_index_start_1(dataframe):
        df_display = dataframe.drop(columns=["Harga Modal"], errors="ignore")  
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "No"
        st.dataframe(df_display)
    
    st.header("Stock Lensa", divider="rainbow")
    tipe_option = [""] + sorted(df_lensa['Tipe'].dropna().unique())
    jenis_option = [""] + sorted(df_lensa['Jenis'].dropna().unique())
    merk_option = [""] + sorted(df_lensa['Merk'].dropna().unique())
    # --- Filter dan tampilkan ---
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    with col1:
        tipe_input = st.selectbox("Tipe", tipe_option)
    with col2:
        jenis_input = st.selectbox("Jenis", jenis_option)
    with col3:
        merk_input = st.selectbox("Merk", merk_option)
    with col4:
        cari = st.button("Cari")
    with col5:
        reset = st.button("Reset")

    if cari:
        filtered_df = df_lensa.copy()
        if tipe_input:
            filtered_df = filtered_df[filtered_df['Tipe'].str.contains(tipe_input, case=False, na=False)]
        if jenis_input:
            filtered_df = filtered_df[filtered_df['Jenis'].str.contains(jenis_input, case=False, na=False)]
        if merk_input:
            filtered_df = filtered_df[filtered_df['Merk'].str.contains(merk_input, case=False, na=False)]

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} data")
            display_df_with_index_start_1(filtered_df)

            csv = filtered_df.drop(columns=["Harga Modal"], errors="ignore").to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download hasil pencarian (.csv)", data=csv, file_name='hasil_pencarian_lensa.csv', mime='text/csv')
        else:
            st.warning("Tidak ditemukan data yang sesuai.")
    elif reset:
        st.info("Menampilkan seluruh data")
        display_df_with_index_start_1(df_lensa)

        csv = df_lensa.drop(columns=["Harga Modal"], errors="ignore").to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download seluruh data (.csv)", data=csv, file_name='database_lensa.csv', mime='text/csv')
    else:
        display_df_with_index_start_1(df_lensa)
    
    tampilkan_lensa_sisa = st.checkbox("🔍 Tampilkan lensa yang perlu cepat")
    if tampilkan_lensa_sisa:
        display_df_with_index_start_1(df_lensa_cepat)
        
        
    tampilkan_stock_rendah = st.checkbox("🔍 Tampilkan lensa perlu restock")
    if tampilkan_stock_rendah:
        df_lensa['Stock'] = pd.to_numeric(df_lensa['Stock'], errors='coerce')
        df_stock_rendah = df_lensa[df_lensa['Stock'] <= 1]
        if not df_stock_rendah.empty:
            st.warning(f"Ditemukan {len(df_stock_rendah)} lensa dengan stock ≤ 1")
            display_df_with_index_start_1(df_stock_rendah)

            csv_stock = df_stock_rendah.drop(columns=["Harga Modal"], errors="ignore").to_csv(index=False).encode('utf-8')

            st.download_button("⬇️ Download lensa stock rendah (.csv)", data=csv_stock, file_name='stock_lensa_rendah.csv', mime='text/csv')
        else:
            st.success("Stock Lensa Aman")
        st.stop()