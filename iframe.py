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
    # AMBIL DATA FRESH
    # ==============================
    df = get_table_raw("frames")

    if df.empty:
        st.info("Belum ada data frame.")
        return

    df = df.sort_values(["merk", "kode"]).reset_index(drop=True)
    df["kode"] = df["kode"].astype(str)

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
        jumlah_input = st.number_input("Jumlah", min_value=1, step=1)

        if st.button("Tambah"):

            row = filtered_df[filtered_df["kode"] == selected_kode]

            if row.empty:
                st.error("Kode tidak ditemukan.")
                return

            row_id = int(row["id"].values[0])
            stock_lama = int(row["stock"].values[0])
            stock_baru = stock_lama + jumlah_input

            response = supabase.table("frames") \
                .update({"stock": stock_baru}) \
                .eq("id", row_id) \
                .execute()

            if not response.data:
                st.error("Update gagal! Cek constraint atau struktur tabel.")
                st.write(response)
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
    # TAMBAH MERK
    # ====================================================
    elif mode == "Tambah Merk":

        selected_merk = st.text_input("Masukan Merk Baru")
        selected_kode = st.text_input("Masukan Kode Baru")
        distributor = st.text_input("Masukan Nama Distributor")
        harga_modal = st.number_input("Harga Modal", min_value=0, step=1000)
        harga_jual = st.number_input("Harga Jual", min_value=0, step=1000)
        stock_baru = st.number_input("Jumlah", min_value=0, step=1)

        if st.button("Tambah"):

            if selected_merk.lower() in df["merk"].str.lower().unique():
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
                st.error("Insert gagal! Cek constraint atau struktur tabel.")
                st.write(response)
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
    # TAMBAH KODE
    # ====================================================
    elif mode == "Tambah Kode":

        selected_merk = st.selectbox("Pilih Merk Frame:", merk_list)

        # Ambil distributor otomatis dari merk tersebut
        distributor = df[df["merk"] == selected_merk]["distributor"].iloc[0]

        selected_kode = st.text_input("Masukan Kode Baru")

        harga_modal = st.number_input("Harga Modal", min_value=0, step=1000)
        harga_jual = st.number_input("Harga Jual", min_value=0, step=1000)
        stock_baru = st.number_input("Jumlah", min_value=0, step=1)

        if st.button("Tambah"):

            if ((df["merk"] == selected_merk) &
                (df["kode"] == selected_kode)).any():
                st.warning("Kode sudah terdaftar untuk merk ini.")
                return

            response = supabase.table("frames").insert({
                "merk": selected_merk,
                "kode": selected_kode,
                "distributor": distributor,  # 🔥 ambil otomatis
                "harga_modal": harga_modal,
                "harga_jual": harga_jual,
                "stock": stock_baru
            }).execute()

            if not response.data:
                st.error("Insert gagal!")
                st.write(response)
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
    # EXPANDER DI PALING BAWAH
    # ==============================
    if st.session_state.last_action:

        with st.expander("📦 Update Berhasil", expanded=True):
            for key, value in st.session_state.last_action.items():
                st.markdown(f"**{key}**: {value}")

        st.session_state.last_action = None