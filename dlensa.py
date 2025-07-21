import streamlit as st
import pandas as pd
from utils import get_dataframe
from constants import SHEET_KEY, SHEET_NAMES

def run():
    @st.cache_data(ttl=300)
    def show_data():
        return get_dataframe(SHEET_KEY, SHEET_NAMES['dlensa'])


    st.title("🕶️ Database Lensa")

    
    df = show_data()
    
    def display_df_with_index_start_1(dataframe):
        df_display = dataframe.reset_index(drop=True)
        df_display.index = df_display.index + 1
        st.dataframe(df_display)
    
    # --- Filter dan tampilkan ---
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    with col1:
        tipe_input = st.text_input("Tipe", placeholder="Contoh: Progressive")
    with col2:
        jenis_input = st.text_input("Jenis", placeholder="Contoh: Bluray")
    with col3:
        merk_input = st.text_input("Merk", placeholder="Contoh: Domas")
    with col4:
        cari = st.button("Cari")
    with col5:
        reset = st.button("Reset")

    if cari:
        filtered_df = df.copy()
        if tipe_input:
            filtered_df = filtered_df[filtered_df['Tipe'].str.contains(tipe_input, case=False, na=False)]
        if jenis_input:
            filtered_df = filtered_df[filtered_df['Jenis'].str.contains(jenis_input, case=False, na=False)]
        if merk_input:
            filtered_df = filtered_df[filtered_df['Merk'].str.contains(merk_input, case=False, na=False)]

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} data")
            display_df_with_index_start_1(filtered_df)

            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download hasil pencarian (.csv)", data=csv, file_name='hasil_pencarian_lensa.csv', mime='text/csv')
        else:
            st.warning("Tidak ditemukan data yang sesuai.")
    elif reset:
        st.info("Menampilkan seluruh data")
        display_df_with_index_start_1(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download seluruh data (.csv)", data=csv, file_name='database_lensa.csv', mime='text/csv')
    else:
        display_df_with_index_start_1(df)
        
    tampilkan_stock_rendah = st.checkbox("🔍 Tampilkan lensa dengan stock ≤ 1")
    if tampilkan_stock_rendah:
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce')
        df_stock_rendah = df[df['Stock'] <= 1]
        if not df_stock_rendah.empty:
            st.warning(f"Ditemukan {len(df_stock_rendah)} lensa dengan stock ≤ 1")
            display_df_with_index_start_1(df_stock_rendah)

            csv_stock = df_stock_rendah.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download lensa stock rendah (.csv)", data=csv_stock, file_name='stock_lensa_rendah.csv', mime='text/csv')
        else:
            st.success("Stock Lensa Aman")
        st.stop()