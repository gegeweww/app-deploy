import streamlit as st
from utils import get_dataframe
from constants import SHEET_KEY, SHEET_NAMES

def run():
    @st.cache_data(ttl=300)
    def show_data():
        return get_dataframe(SHEET_KEY, SHEET_NAMES['dframe'])

    st.title("📦 Database Frame")
    df = show_data()

    def display_df_with_index_start_1(dataframe):
        df_display = dataframe.reset_index(drop=True)
        df_display.index = df_display.index + 1
        st.dataframe(df_display)

    # --- Filter dan tampilkan ---
    col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
    with col1:
        merk_input = st.text_input("Merk", placeholder="Contoh: Levi's")
    with col2:
        kode_input = st.text_input("Kode", placeholder="Contoh: LV001")
    with col3:
        cari = st.button("Cari")
    with col4:
        reset = st.button("Reset")

    if cari:
        filtered_df = df.copy()
        if merk_input:
            filtered_df = filtered_df[filtered_df['Merk'].str.contains(merk_input, case=False, na=False)]
        if kode_input:
            filtered_df = filtered_df[filtered_df['Kode'].astype(str).str.contains(kode_input, case=False, na=False)]

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} data")
            display_df_with_index_start_1(filtered_df)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download hasil pencarian (.csv)", data=csv, file_name='hasil_pencarian.csv', mime='text/csv')
        else:
            st.warning("Tidak ditemukan data yang sesuai.")
    elif reset:
        st.info("Menampilkan seluruh data")
        display_df_with_index_start_1(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download seluruh data (.csv)", data=csv, file_name='database_frame.csv', mime='text/csv')
    else:
        display_df_with_index_start_1(df)
