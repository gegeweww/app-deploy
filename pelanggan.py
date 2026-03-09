import streamlit as st
import pandas as pd
from utils import get_table_cached, get_supabase


def run():
    st.title("Database Pelanggan")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ==============================
    # Ambil Data dari Supabase
    # ==============================
    df_transaksi = get_table_cached("transaksi_detail")
    df_pelanggan = get_table_cached("pelanggan")
    
    if df_transaksi.empty or df_pelanggan.empty:
        st.warning("Data belum tersedia.")
        return

    # Merge pelanggan
    df = df_transaksi.merge(
        df_pelanggan[["id_pelanggan", "no_hp"]],
        on="id_pelanggan",
        how="left"
    )

    df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")

    lens_cols = [
        "sph_r", "cyl_r", "axis_r", "add_r",
        "sph_l", "cyl_l", "axis_l", "add_l"
    ]

    for col in lens_cols:
        df[col] = df[col].astype(str).fillna("")

    results = []

    for cust_id, group in df.groupby("id_pelanggan"):
        group = group.dropna(subset=["tanggal"])
        if group.empty:
            continue

        ukuran_group = group.groupby(lens_cols)

        for _, transaksi_group in ukuran_group:
            if transaksi_group.empty:
                continue

            last_row = transaksi_group.sort_values("tanggal").iloc[-1]

            def format_mata(sph, cyl, axis):
                try:
                    axis = str(int(float(axis))) if axis not in ["", None, "None"] else ""
                except:
                    axis = str(axis)

                if cyl in ["0", "0.0", "0.00", "", "None", None]:
                    return f"{sph}"
                return f"{sph} / {cyl} × {axis}"

            results.append({
                "ID Pelanggan": cust_id,
                "Nama": last_row["nama"],
                "No HP": last_row["no_hp"],
                "Mata R": format_mata(last_row["sph_r"], last_row["cyl_r"], last_row["axis_r"]),
                "Mata L": format_mata(last_row["sph_l"], last_row["cyl_l"], last_row["axis_l"]),
                "Add": last_row["add_r"],
                "Tanggal Terakhir": last_row["tanggal"]
            })

    if not results:
        st.warning("Belum ada data ukuran.")
        return

    df_final = pd.DataFrame(results)
    df_final = df_final.sort_values("ID Pelanggan", ascending=True)

    # ==============================
    # SEARCH
    # ==============================
    search = st.text_input("Cari Nama atau No HP", placeholder="Ketik untuk mencari...")

    if st.button("Reset"):
        st.session_state["search_pelanggan"] = ""
        st.rerun()

    query = st.session_state.get("search_pelanggan", search)

    if search:
        st.session_state["search_pelanggan"] = search
        df_final = df_final[
            df_final["Nama"].str.contains(search, case=False, na=False) |
            df_final["No HP"].str.contains(search, case=False, na=False)
        ]

    df_final = df_final.reset_index(drop=True)
    df_final.index = df_final.index + 1
    df_final.index.name = "No"

    st.dataframe(df_final, use_container_width=True)

    df_pel = df_pelanggan.copy()
    df_pel.columns = df_pel.columns.str.lower()
    df_pel = df_pel.sort_values("nama").reset_index(drop=True)
    
    # ==============================
    # EDIT NO HP
    # ==============================
    st.subheader("✏️ Update No HP Pelanggan")

    col1, col2 = st.columns(2)
    with col1:
        cari_nama = st.text_input("Cari by Nama", placeholder="contoh: budi", key="cari_nama_edit")
    with col2:
        cari_id = st.text_input("Cari by ID Pelanggan", placeholder="contoh: OM001", key="cari_id_edit")

    df_hasil = df_pel.copy()
    if cari_nama:
        df_hasil = df_hasil[df_hasil["nama"].str.contains(cari_nama.strip().lower(), case=False, na=False)]
    if cari_id:
        df_hasil = df_hasil[df_hasil["id_pelanggan"].str.contains(cari_id.strip().upper(), case=False, na=False)]

    if cari_nama or cari_id:
        if df_hasil.empty:
            st.warning("Pelanggan tidak ditemukan.")
        else:
            st.markdown(f"**{len(df_hasil)} pelanggan ditemukan**")
            for _, row in df_hasil.iterrows():
                id_pel = row["id_pelanggan"]
                nama = row["nama"]
                no_hp = row["no_hp"]

                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{nama.title()}** `{id_pel}`")
                        st.markdown(f"📱 {no_hp}")
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{id_pel}"):
                            st.session_state["edit_pelanggan"] = id_pel

                if st.session_state.get("edit_pelanggan") == id_pel:
                    with st.container(border=True):
                        st.markdown(f"**Update No HP — {nama.title()}**")
                        st.markdown(f"No HP saat ini: `{no_hp}`")

                        no_hp_baru = st.text_input(
                            "No HP Baru",
                            value=no_hp if no_hp != "0" else "",
                            key=f"input_hp_{id_pel}",
                            placeholder="contoh: 08123456789"
                        )

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Simpan", key=f"simpan_{id_pel}"):
                                if not no_hp_baru.strip():
                                    st.warning("No HP tidak boleh kosong.")
                                elif no_hp_baru.strip() == no_hp:
                                    st.info("No HP tidak berubah.")
                                else:
                                    supabase = get_supabase()
                                    supabase.table("pelanggan") \
                                        .update({"no_hp": no_hp_baru.strip()}) \
                                        .eq("id_pelanggan", id_pel) \
                                        .execute()
                                    st.success(f"No HP {nama.title()} berhasil diupdate!")
                                    st.session_state.pop("edit_pelanggan", None)
                                    st.cache_data.clear()
                                    st.rerun()
                        with col_cancel:
                            if st.button("❌ Batal", key=f"batal_{id_pel}"):
                                st.session_state.pop("edit_pelanggan", None)
                                st.rerun()