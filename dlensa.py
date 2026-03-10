import streamlit as st
import pandas as pd
from utils import get_table_cached


def run():

    st.title(":goggles: Database Lensa")

    # ==============================
    # AMBIL DATA DARI SUPABASE
    # ==============================
    df_lensa = get_table_cached("lensa")
    df_lensa_cepat = get_table_cached("perlu_habis")
    df_harga = get_table_cached("harga_lensa")

    # ==============================
    # VALIDASI DATA
    # ==============================
    if df_lensa.empty:
        st.info("Belum ada data lensa.")
        return
    if not df_lensa.empty:
        df_lensa = df_lensa.sort_values("id").reset_index(drop=True)

    # Rapikan nama kolom (lowercase database)
    df_lensa.columns = df_lensa.columns.str.lower()
    df_lensa_cepat.columns = df_lensa_cepat.columns.str.lower()
    df_harga.columns = df_harga.columns.str.lower()

    # ==============================
    # HARGA LENSA
    # ==============================
    st.header("Harga Lensa", divider="rainbow")

    def format_rupiah_columns(df):
        df_copy = df.copy()

        for col in df_copy.columns:
            if "harga" in col.lower():
                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce") \
                    .fillna(0) \
                    .apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))

        return df_copy

    if not df_harga.empty:

        df_harga_display = format_rupiah_columns(df_harga)
        df_harga_display = df_harga_display.drop(columns=["id", "harga_modal","harga_reseller"], errors="ignore")

        df_harga_display = df_harga_display.reset_index(drop=True)
        df_harga_display.index = df_harga_display.index + 1
        df_harga_display.index.name = "No"

        df_harga_display.columns = [
            col.replace("_", " ").title()
            for col in df_harga_display.columns
        ]

        st.dataframe(df_harga_display, width='stretch')

    else:
        st.warning("Data harga lensa kosong.")

    # ==============================
    # FUNCTION DISPLAY
    # ==============================
    def display_df_with_index_start_1(dataframe):

        df_display = format_rupiah_columns(dataframe)
        df_display = df_display.drop(columns=["id", "harga_modal","harga_reseller"], errors="ignore")
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "No"

        df_display.columns = [
            col.replace("_", " ").title()
            for col in df_display.columns
        ]

        st.dataframe(df_display, width='stretch')

    # ==============================
    # STOCK LENSA
    # ==============================
    st.header("Stock Lensa", divider="rainbow")

    tipe_option = [""] + sorted(df_lensa["tipe"].dropna().unique())
    jenis_option = [""] + sorted(df_lensa["jenis"].dropna().unique())
    merk_option = [""] + sorted(df_lensa["merk"].dropna().unique())

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

    filtered_df = df_lensa.copy()

    if cari:
        if tipe_input:
            filtered_df = filtered_df[
                filtered_df["tipe"].str.contains(tipe_input, case=False, na=False)
            ]
        if jenis_input:
            filtered_df = filtered_df[
                filtered_df["jenis"].str.contains(jenis_input, case=False, na=False)
            ]
        if merk_input:
            filtered_df = filtered_df[
                filtered_df["merk"].str.contains(merk_input, case=False, na=False)
            ]

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} data")
            display_df_with_index_start_1(filtered_df)

            csv = filtered_df.drop(columns=["id","harga_modal","harga_reseller"], errors="ignore") \
                .to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download hasil pencarian (.csv)",
                data=csv,
                file_name="hasil_pencarian_lensa.csv",
                mime="text/csv"
            )
        else:
            st.warning("Tidak ditemukan data yang sesuai.")

    elif reset:
        st.info("Menampilkan seluruh data")
        display_df_with_index_start_1(df_lensa)

    else:
        display_df_with_index_start_1(df_lensa)

    # ==============================
    # LENSA PERLU CEPAT
    # ==============================
    tampilkan_lensa_sisa = st.checkbox("🔍 Tampilkan lensa yang perlu cepat")

    if tampilkan_lensa_sisa and not df_lensa_cepat.empty:
        display_df_with_index_start_1(df_lensa_cepat)

    # ==============================
    # STOCK RENDAH
    # ==============================
    tampilkan_stock_rendah = st.checkbox("🔍 Tampilkan lensa perlu restock")

    if tampilkan_stock_rendah:

        df_lensa["stock"] = pd.to_numeric(df_lensa["stock"], errors="coerce")

        df_stock_rendah = df_lensa[df_lensa["stock"] <= 1]

        if not df_stock_rendah.empty:
            st.warning(f"Ditemukan {len(df_stock_rendah)} lensa dengan stock ≤ 1")
            display_df_with_index_start_1(df_stock_rendah)

            csv_stock = df_stock_rendah.drop(columns=["id","harga_modal","harga_reseller"], errors="ignore") \
                .to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download lensa stock rendah (.csv)",
                data=csv_stock,
                file_name="stock_lensa_rendah.csv",
                mime="text/csv"
            )
        else:
            st.success("Stock Lensa Aman")