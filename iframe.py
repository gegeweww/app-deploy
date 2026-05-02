import streamlit as st
from utils import get_table_raw, get_supabase, catat_logframe_supabase


def run():
    st.title("➕ Input / Edit Stock Frame")
    st.write("Tambahkan atau ubah stock dari frame yang tersedia")

    if "last_action" not in st.session_state:
        st.session_state.last_action = None

    user = st.session_state.get("user", "Unknown")
    supabase = get_supabase()

    # ==============================
    # REFRESH
    # ==============================
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ==============================
    # AMBIL DATA FRESH
    # ==============================
    df = get_table_raw("frames")

    if df.empty:
        st.info("Belum ada data frame.")
        return

    df.columns = df.columns.str.lower()
    df = df.sort_values(["merk", "kode"]).reset_index(drop=True)
    df["kode"] = df["kode"].astype(str)
    df["merk"] = df["merk"].astype(str).str.strip()

    merk_list = sorted(df["merk"].dropna().unique())

    mode = st.selectbox(
        "Pilih Mode:",
        ["Tambah Stock", "Tambah Merk", "Tambah Kode"]
    )

    # ====================================================
    # TAMBAH STOCK
    # ====================================================
    if mode == "Tambah Stock":

        selected_merk = st.selectbox("Pilih Merk Frame:", merk_list)

        filtered_df = df[df["merk"] == selected_merk]
        kode_list = sorted(filtered_df["kode"].unique())

        selected_kode = st.selectbox("Pilih Kode Frame:", kode_list)

        jumlah_input = int(
            st.number_input(
                "Jumlah",
                min_value=1,
                step=1
            )
        )

        if st.button("Tambah Stock"):

            row = filtered_df[filtered_df["kode"] == selected_kode]

            if row.empty:
                st.error("Kode tidak ditemukan.")
                return

            row_id = int(row["id"].values[0])
            stock_lama = int(row["stock"].values[0] or 0)
            stock_baru = stock_lama + jumlah_input

            response = (
                supabase.table("frames")
                .update({"stock": int(stock_baru)})
                .eq("id", row_id)
                .execute()
            )

            if not response.data:
                st.error("Update gagal.")
                return

            catat_logframe_supabase(
                merk=selected_merk,
                kode=selected_kode,
                source="iframe",
                mode="Tambah Stock",
                jumlah_input=jumlah_input,
                stock_lama=stock_lama,
                stock_baru=stock_baru,
                user=user
            )

            st.session_state.last_action = {
                "Merk": selected_merk,
                "Kode": selected_kode,
                "Ditambahkan": jumlah_input,
                "Total Sekarang": stock_baru
            }

            st.rerun()

    # ====================================================
    # TAMBAH MERK BARU
    # ====================================================
    elif mode == "Tambah Merk":

        selected_merk = st.text_input("Masukkan Merk Baru").strip()
        selected_kode = st.text_input("Masukkan Kode Baru").strip()
        distributor = st.text_input("Masukkan Nama Distributor").strip()

        harga_modal = int(
            st.number_input("Harga Modal", min_value=0, step=1000)
        )

        harga_jual = int(
            st.number_input("Harga Jual", min_value=0, step=1000)
        )

        stock_baru = int(
            st.number_input("Jumlah", min_value=0, step=1)
        )

        if st.button("Tambah Merk"):

            if not selected_merk or not selected_kode:
                st.warning("Merk dan kode wajib diisi.")
                return

            existing_merk = df["merk"].str.lower().str.strip().unique()

            if selected_merk.lower() in existing_merk:
                st.warning("Merk sudah terdaftar.")
                return

            response = supabase.table("frames").insert({
                "merk": selected_merk,
                "kode": selected_kode,
                "distributor": distributor,
                "harga_modal": harga_modal,
                "harga_jual": harga_jual,
                "stock": stock_baru
            }).execute()

            if not response.data:
                st.error("Insert gagal.")
                return

            catat_logframe_supabase(
                merk=selected_merk,
                kode=selected_kode,
                source="iframe",
                mode="Tambah Merk",
                stock_baru=stock_baru,
                user=user
            )

            st.session_state.last_action = {
                "Merk": selected_merk,
                "Kode": selected_kode,
                "Stock": stock_baru
            }

            st.rerun()

    # ====================================================
    # TAMBAH KODE BARU
    # ====================================================
    elif mode == "Tambah Kode":

        selected_merk = st.selectbox(
            "Pilih Merk Frame:",
            merk_list
        )

        distributor_row = df[df["merk"] == selected_merk]

        distributor = (
            distributor_row["distributor"].iloc[0]
            if not distributor_row.empty
            else ""
        )

        st.text_input(
            "Distributor",
            value=distributor,
            disabled=True
        )

        selected_kode = st.text_input(
            "Masukkan Kode Baru"
        ).strip()

        harga_modal = int(
            st.number_input("Harga Modal", min_value=0, step=1000)
        )

        harga_jual = int(
            st.number_input("Harga Jual", min_value=0, step=1000)
        )

        stock_baru = int(
            st.number_input("Jumlah", min_value=0, step=1)
        )

        if st.button("Tambah Kode"):

            if not selected_kode:
                st.warning("Kode wajib diisi.")
                return

            duplicate = df[
                (df["merk"].str.lower() == selected_merk.lower()) &
                (df["kode"].str.lower() == selected_kode.lower())
            ]

            if not duplicate.empty:
                st.warning("Kode sudah terdaftar untuk merk ini.")
                return

            response = supabase.table("frames").insert({
                "merk": selected_merk,
                "kode": selected_kode,
                "distributor": distributor,
                "harga_modal": harga_modal,
                "harga_jual": harga_jual,
                "stock": stock_baru
            }).execute()

            if not response.data:
                st.error("Insert gagal.")
                return

            catat_logframe_supabase(
                merk=selected_merk,
                kode=selected_kode,
                source="iframe",
                mode="Tambah Kode",
                stock_baru=stock_baru,
                user=user
            )

            st.session_state.last_action = {
                "Merk": selected_merk,
                "Kode": selected_kode,
                "Distributor": distributor,
                "Stock": stock_baru
            }

            st.rerun()

    # ==============================
    # RINGKASAN ACTION
    # ==============================
    if st.session_state.last_action:
        with st.expander("✅ Update Berhasil", expanded=True):
            for key, value in st.session_state.last_action.items():
                st.markdown(f"**{key}**: {value}")

        st.session_state.last_action = None