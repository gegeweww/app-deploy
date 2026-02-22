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

        st.dataframe(df_display, use_container_width=True)

    # ==============================
    # FILTER SECTION
    # ==============================
    col1, col2, col3, col4 = st.columns([3, 3, 1, 1])

    with col1:
        merk_input = st.text_input("Merk", placeholder="Contoh: Levi's")

    with col2:
        kode_input = st.text_input("Kode", placeholder="Contoh: LV001")

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
            filtered_df = filtered_df[
                filtered_df["merk"].str.contains(merk_input, case=False, na=False)
            ]

        if kode_input:
            filtered_df = filtered_df[
                filtered_df["kode"].astype(str).str.contains(kode_input, case=False, na=False)
            ]

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