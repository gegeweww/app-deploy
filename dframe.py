import streamlit as st
from utils import get_table_cached


def run():

    st.title("🕶️ Database Frame")

    # ==============================
    # AMBIL DATA DARI SUPABASE
    # ==============================
    df = get_table_cached("frames")

    if df.empty:
        st.info("Belum ada data frame.")
        return

    # Rapikan & sort
    df = df.sort_values(["merk", "kode"]).reset_index(drop=True)

    # ==============================
    # FUNCTION TAMPIL DATA
    # ==============================
    def display_df_with_index_start_1(dataframe):

        df_display = dataframe.drop(columns=["id", "harga_modal"], errors="ignore")
        df_display = df_display.reset_index(drop=True)
        df_display["harga_jual"] = df_display["harga_jual"] \
            .apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        df_display.index = df_display.index + 1
        df_display.index.name = "No"

        # Beautify header
        df_display.columns = [col.replace("_", " ").title() for col in df_display.columns]

        st.dataframe(df_display, width='stretch')

    # ==============================
    # FILTER SECTION
    # ==============================

    col1, col2, col3, col4 = st.columns([3, 3, 1, 1])

    # Options merk dari semua data
    merk_options = sorted(df["merk"].dropna().unique().tolist())

    with col1:
        merk_input = st.selectbox(
            "Merk",
            options=[""] + merk_options,
            index=0,
            placeholder="Contoh: Levi's",
            key="merk_input_frame"
        )

    # Filter kode berdasarkan merk yang dipilih
    if merk_input:
        df_kode_filtered = df[df["merk"] == merk_input]
    else:
        df_kode_filtered = df

    kode_options = sorted(df_kode_filtered["kode"].dropna().unique().tolist())

    with col2:
        kode_input = st.selectbox(
            "Kode",
            options=[""] + kode_options,
            index=0,
            placeholder="Contoh: LV001",
            key="kode_input_frame"
        )

    with col3:
        cari = st.button("Cari")

    with col4:
        reset = st.button("Reset")

    # ==============================
    # LOGIC FILTER
    # ==============================
    filtered_df = df.copy()

    if cari:
        if merk_input:
            filtered_df = filtered_df[filtered_df["merk"] == merk_input]

        if kode_input:
            filtered_df = filtered_df[filtered_df["kode"] == kode_input]

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} data")
            display_df_with_index_start_1(filtered_df)

            csv = filtered_df.drop(columns=["harga_modal"], errors="ignore") \
                .to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download hasil pencarian (.csv)",
                data=csv,
                file_name="hasil_pencarian.csv",
                mime="text/csv"
            )
        else:
            st.warning("Tidak ditemukan data yang sesuai.")

    elif reset:
        st.info("Menampilkan seluruh data")
        display_df_with_index_start_1(df)

    else:
        display_df_with_index_start_1(df)