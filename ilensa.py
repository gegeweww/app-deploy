import streamlit as st
from datetime import datetime
from utils import get_table_raw, get_supabase, catat_loglensa_supabase


def run():

    st.title("➕ Input Stock Lensa")
    st.write("Tambahkan stock dari lensa yang tersedia")

    # ==============================
    # SESSION STATE UNTUK EXPANDER
    # ==============================
    if "last_lensa_action" not in st.session_state:
        st.session_state.last_lensa_action = None

    user = st.session_state.get("user", "Unknown")
    supabase = get_supabase()

    # ==============================
    # AMBIL DATA DARI SUPABASE
    # ==============================
    df_lensa = get_table_raw("lensa")

    if df_lensa.empty:
        st.info("Belum ada data lensa.")
        return

    df_lensa = df_lensa.sort_values(
        ["tipe", "jenis", "merk", "sph", "cyl", "add_power"]
    ).reset_index(drop=True)

    # ==============================
    # DROPDOWN OPTIONS
    # ==============================
    tipe_list = sorted(df_lensa["tipe"].dropna().unique())

    selected_tipe = st.selectbox(
        "Pilih Tipe Lensa:",
        tipe_list,
        index=tipe_list.index("Single Vision") if "Single Vision" in tipe_list else 0
    )

    df_filtered = df_lensa[df_lensa["tipe"] == selected_tipe]

    jenis_list = sorted(df_filtered["jenis"].dropna().unique())
    merk_list = sorted(df_filtered["merk"].dropna().unique())
    sph_list = sorted(df_filtered["sph"].astype(str).unique())
    cyl_list = sorted(df_filtered["cyl"].astype(str).unique())
    add_list = sorted(df_filtered["add_power"].astype(str).unique())

    selected_jenis = st.selectbox(
        "Pilih Jenis Lensa:",
        jenis_list,
        index=jenis_list.index("HMC") if "HMC" in jenis_list else 0
    )

    selected_merk = st.selectbox(
        "Pilih Merk Lensa:",
        merk_list,
        index=merk_list.index("Domas") if "Domas" in merk_list else 0
    )

    selected_sph = st.selectbox(
        "Pilih SPH:",
        sph_list,
        index=sph_list.index("0.00") if "0.00" in sph_list else 0
    )

    selected_cyl = st.selectbox(
        "Pilih CYL:",
        cyl_list,
        index=cyl_list.index("0.00") if "0.00" in cyl_list else 0
    )

    if selected_tipe == "Single Vision":
        selected_add = ""
    else:
        selected_add = st.selectbox("Pilih Add:", add_list)

    jumlah_input = st.number_input("Jumlah", min_value=1, step=1)

    # ==============================
    # TAMBAH STOCK
    # ==============================
    if st.button("Tambah"):

        filter_stock = df_lensa[
            (df_lensa["jenis"] == selected_jenis) &
            (df_lensa["tipe"] == selected_tipe) &
            (df_lensa["merk"] == selected_merk) &
            (df_lensa["sph"] == str(selected_sph)) &
            (df_lensa["cyl"] == str(selected_cyl))
        ]

        # Handle add_power
        if selected_tipe == "Single Vision":
            filter_stock = filter_stock[
                df_lensa["add_power"].isna()
            ]
        else:
            filter_stock = filter_stock[
                df_lensa["add_power"] == str(selected_add)
            ]

        stock_lama = int(filter_stock["stock"].values[0])
        stock_baru = stock_lama + jumlah_input

        # ==============================
        # UPDATE STOCK DI SUPABASE
        # ==============================
        query = supabase.table("lensa") \
            .update({"stock": stock_baru}) \
            .eq("jenis", selected_jenis) \
            .eq("tipe", selected_tipe) \
            .eq("merk", selected_merk) \
            .eq("sph", selected_sph) \
            .eq("cyl", selected_cyl)

        if selected_tipe == "Single Vision":
            query = query.is_("add_power", None)
        else:
            query = query.eq("add_power", selected_add)

        query.execute()

        # ==============================
        # CATAT LOG
        # ==============================
        catat_loglensa_supabase(
            jenis=selected_jenis,
            tipe=selected_tipe,
            merk=selected_merk,
            sph=selected_sph,
            cyl=selected_cyl,
            add_power=selected_add,
            source="ilensa",
            jumlah_input=jumlah_input,
            stock_lama=stock_lama,
            stock_baru=stock_baru,
            user=user
        )

        # ==============================
        # SIMPAN UNTUK EXPANDER
        # ==============================
        st.session_state.last_lensa_action = {
            "Jenis": selected_jenis,
            "Tipe": selected_tipe,
            "Merk": selected_merk,
            "SPH": selected_sph,
            "CYL": selected_cyl,
            "Add": selected_add,
            "Ditambahkan": jumlah_input,
            "Total Sekarang": stock_baru
        }

        st.rerun()

    # ==============================
    # TAMPILKAN EXPANDER DI BAWAH
    # ==============================
    if st.session_state.last_lensa_action:

        data = st.session_state.last_lensa_action

        with st.expander("📦 Stock Berhasil Diperbarui", expanded=True):
            for key, value in data.items():
                st.markdown(f"**{key}**: {value}")

        st.session_state.last_lensa_action = None