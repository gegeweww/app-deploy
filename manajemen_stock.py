import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import get_table_cached, get_supabase


def now_jkt():
    return datetime.now(ZoneInfo("Asia/Jakarta")).replace(microsecond=0)


def catat_log_frame(merk, kode, status, keterangan, user):
    supabase = get_supabase()
    supabase.table("log_frames").insert({
        "timestamp_log": now_jkt().strftime("%Y-%m-%d %H:%M:%S"),
        "merk": merk,
        "kode": kode,
        "status": status,
        "keterangan": keterangan,
        "user_name": user
    }).execute()


def catat_log_lensa(tipe, merk, jenis, sph, cyl, add_power, status, keterangan, user):
    supabase = get_supabase()
    supabase.table("log_lensa").insert({
        "timestamp_log": now_jkt().strftime("%Y-%m-%d %H:%M:%S"),
        "tipe": tipe,
        "merk": merk,
        "jenis": jenis,
        "sph": str(sph),
        "cyl": str(cyl),
        "add_power": str(add_power),
        "status": status,
        "keterangan": keterangan,
        "user_name": user
    }).execute()


def run():
    st.title("🗂️ Manajemen Stock")
    user = st.session_state.get("user", "Unknown")

    @st.cache_data(ttl=60)
    def load_frame():
        return get_table_cached("frames")

    @st.cache_data(ttl=60)
    def load_lensa():
        return get_table_cached("lensa")

    df_frame = load_frame()
    df_frame.columns = df_frame.columns.str.lower()

    df_lensa = load_lensa()
    df_lensa.columns = df_lensa.columns.str.lower()

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ==============================
    # NAVIGASI UTAMA
    # ==============================
    pilih_tab = st.selectbox("Kategori", ["🖼️ Stock Frame", "🔬 Stock Lensa"], key="tab_manajemen")

    st.divider()

    # ==============================
    # STOCK FRAME
    # ==============================
    if pilih_tab == "🖼️ Stock Frame":

        pilih_subtab = st.selectbox("Menu", ["✏️ Edit Stock", "↩️ Retur"], key="subtab_frame")

        st.divider()

        # ==============================
        # EDIT STOCK FRAME
        # ==============================
        if pilih_subtab == "✏️ Edit Stock":
            st.subheader("✏️ Edit Stock Frame")
            
            merk_options_frame = sorted(df_frame["merk"].dropna().unique().tolist())

            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                cari_merk = st.selectbox("Cari by Merk", options=[""] +  merk_options_frame, index=0, placeholder="contoh: ACK EYEWEAR", key="cari_merk_frame")

            # Filter kode options berdasarkan merk yang dipilih
            if cari_merk:
                df_kode_filtered = df_frame[df_frame["merk"] == cari_merk]
            else:
                df_kode_filtered = df_frame

            kode_options_frame = sorted(df_kode_filtered["kode"].dropna().unique().tolist())
            
            with col2:
                cari_kode = st.selectbox("Cari by Kode", options=[""] +  kode_options_frame, index=0, placeholder="contoh: 116", key="cari_kode_frame")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Reset", key="reset_frame_edit"):
                    st.session_state.pop("cari_merk_frame", None)
                    st.session_state.pop("cari_kode_frame", None)
                    st.session_state.pop("edit_frame_id", None)
                    st.rerun()

            df_hasil_frame = df_frame.copy()
            if cari_merk:
                df_hasil_frame = df_hasil_frame[df_hasil_frame["merk"].str.contains(cari_merk.strip(), case=False, na=False)]
            if cari_kode:
                df_hasil_frame = df_hasil_frame[df_hasil_frame["kode"].str.contains(cari_kode.strip(), case=False, na=False)]

            if cari_merk or cari_kode:
                if df_hasil_frame.empty:
                    st.warning("Frame tidak ditemukan.")
                else:
                    st.markdown(f"**{len(df_hasil_frame)} frame ditemukan**")
                    for _, row in df_hasil_frame.iterrows():
                        frame_id = row["id"]
                        merk = row["merk"]
                        kode = row["kode"]
                        stock = int(row["stock"] or 0)
                        harga_jual = int(row["harga_jual"] or 0)

                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{merk} — {kode}**")
                                st.markdown(f"Stock: `{stock}` | Harga Jual: `Rp {harga_jual:,}`".replace(",", "."))
                            with col2:
                                if st.button("✏️ Edit", key=f"btn_edit_frame_{frame_id}"):
                                    st.session_state["edit_frame_id"] = frame_id

                        if st.session_state.get("edit_frame_id") == frame_id:
                            with st.container(border=True):
                                st.markdown(f"**Edit — {merk} {kode}**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    merk_baru = st.text_input("Merk", value=merk, key=f"merk_baru_{frame_id}")
                                    kode_baru = st.text_input("Kode", value=kode, key=f"kode_baru_{frame_id}")
                                with col2:
                                    stock_baru = st.number_input("Stock", value=stock, min_value=0, key=f"stock_baru_{frame_id}")
                                    harga_jual_baru = st.number_input("Harga Jual", value=harga_jual, min_value=0, step=1000, key=f"harga_jual_baru_{frame_id}")

                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 Simpan", key=f"simpan_frame_{frame_id}"):
                                        supabase = get_supabase()
                                        supabase.table("frames").update({
                                            "merk": merk_baru.strip(),
                                            "kode": kode_baru.strip(),
                                            "stock": stock_baru,
                                            "harga_jual": harga_jual_baru
                                        }).eq("id", frame_id).execute()

                                        keterangan = (
                                            f"Revisi: merk {merk}→{merk_baru}, "
                                            f"kode {kode}→{kode_baru}, "
                                            f"stock {stock}→{stock_baru}, "
                                            f"harga jual {harga_jual}→{harga_jual_baru}"
                                        )
                                        catat_log_frame(merk_baru, kode_baru, "revisi", keterangan, user)

                                        st.success(f"Frame {merk} {kode} berhasil diupdate!")
                                        st.session_state.pop("edit_frame_id", None)
                                        st.cache_data.clear()
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ Batal", key=f"batal_frame_{frame_id}"):
                                        st.session_state.pop("edit_frame_id", None)
                                        st.rerun()

        # ==============================
        # RETUR FRAME
        # ==============================
        elif pilih_subtab == "↩️ Retur":
            st.subheader("↩️ Retur Frame")

            merk_options_retur = sorted(df_frame["merk"].dropna().unique().tolist())

            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                cari_merk = st.selectbox("Cari by Merk", options=[""] +  merk_options_retur, index=0, placeholder="contoh: ACK EYEWEAR", key="cari_merk_retur")
                
            # Filter kode options berdasarkan merk yang dipilih
            if cari_merk:
                df_kode_filtered = df_frame[df_frame["merk"] == cari_merk]
            else:
                df_kode_filtered = df_frame

            kode_options_retur = sorted(df_kode_filtered["kode"].dropna().unique().tolist())

            with col2:
                cari_kode = st.selectbox("Cari by Kode", options=[""] +  kode_options_retur, index=0, placeholder="contoh: 116", key="cari_kode_retur")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Reset", key="reset_retur"):
                    st.session_state.pop("cari_merk_retur", None)
                    st.session_state.pop("cari_kode_retur", None)
                    st.session_state.pop("retur_frame_id", None)
                    st.rerun()

            df_hasil_retur = df_frame.copy()
            if cari_merk:
                df_hasil_retur = df_hasil_retur[df_hasil_retur["merk"] == cari_merk]
            if cari_kode:
                df_hasil_retur = df_hasil_retur[df_hasil_retur["kode"] == cari_kode]

            if cari_merk or cari_kode:
                if df_hasil_retur.empty:
                    st.warning("Frame tidak ditemukan.")
                else:
                    st.markdown(f"**{len(df_hasil_retur)} frame ditemukan**")
                    for _, row in df_hasil_retur.iterrows():
                        frame_id = row["id"]
                        merk = row["merk"]
                        kode = row["kode"]
                        stock = int(row["stock"] or 0)

                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{merk} — {kode}**")
                                st.markdown(f"Stock saat ini: `{stock}`")
                            with col2:
                                if st.button("↩️ Retur", key=f"btn_retur_{frame_id}"):
                                    st.session_state["retur_frame_id"] = frame_id

                        if st.session_state.get("retur_frame_id") == frame_id:
                            with st.container(border=True):
                                st.markdown(f"**Retur — {merk} {kode}**")
                                st.markdown(f"Stock saat ini: `{stock}`")

                                jumlah_retur = st.number_input(
                                    "Jumlah Retur",
                                    min_value=1,
                                    max_value=max(stock, 1),
                                    value=1,
                                    key=f"jumlah_retur_{frame_id}"
                                )
                                keterangan_retur = st.text_input(
                                    "Keterangan",
                                    placeholder="contoh: frame cacat, retak",
                                    key=f"ket_retur_{frame_id}"
                                )

                                stock_baru = stock - jumlah_retur
                                st.markdown(f"Stock setelah retur: `{stock_baru}`")

                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 Simpan", key=f"simpan_retur_{frame_id}"):
                                        supabase = get_supabase()
                                        supabase.table("frames").update({
                                            "stock": stock_baru
                                        }).eq("id", frame_id).execute()

                                        keterangan = f"Retur {jumlah_retur} pcs, stock {stock}→{stock_baru}. {keterangan_retur}"
                                        catat_log_frame(merk, kode, "retur", keterangan, user)

                                        st.success(f"Retur {merk} {kode} berhasil! Stock: {stock} → {stock_baru}")
                                        st.session_state.pop("retur_frame_id", None)
                                        st.cache_data.clear()
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ Batal", key=f"batal_retur_{frame_id}"):
                                        st.session_state.pop("retur_frame_id", None)
                                        st.rerun()

    # ==============================
    # STOCK LENSA
    # ==============================
    elif pilih_tab == "🔬 Stock Lensa":
        st.subheader("✏️ Edit Stock Lensa")
        
        merk_options_lensa = sorted(df_lensa["merk"].dropna().unique().tolist())
        tipe_options_lensa = sorted(df_lensa["tipe"].dropna().unique().tolist())
        jenis_options_lensa = sorted(df_lensa["jenis"].dropna().unique().tolist())
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            cari_merk_lensa = st.selectbox("Cari by Merk", options=[None] + merk_options_lensa, placeholder="contoh: Domas", key="cari_merk_lensa")
        with col2:
            cari_tipe_lensa = st.selectbox("Cari by Tipe", options=[None] + tipe_options_lensa, placeholder="contoh: Progressive", key="cari_tipe_lensa")
        with col3:
            cari_jenis_lensa = st.selectbox("Cari by Jenis", options=[None] + jenis_options_lensa, placeholder="contoh: Bluray", key="cari_jenis_lensa")
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Reset", key="reset_lensa_edit"):
                st.session_state.pop("cari_merk_lensa", None)
                st.session_state.pop("cari_tipe_lensa", None)
                st.session_state.pop("cari_jenis_lensa", None)
                st.session_state.pop("edit_lensa_id", None)
                st.rerun()

        df_hasil_lensa = df_lensa.copy()
        if cari_merk_lensa:
            df_hasil_lensa = df_hasil_lensa[df_hasil_lensa["merk"] == cari_merk_lensa]
        if cari_tipe_lensa:
            df_hasil_lensa = df_hasil_lensa[df_hasil_lensa["tipe"] == cari_tipe_lensa]
        if cari_jenis_lensa:
            df_hasil_lensa = df_hasil_lensa[df_hasil_lensa["jenis"] == cari_jenis_lensa]
        
        if cari_merk_lensa or cari_tipe_lensa or cari_jenis_lensa:
            if df_hasil_lensa.empty:
                st.warning("Lensa tidak ditemukan.")
            else:
                st.markdown(f"**{len(df_hasil_lensa)} lensa ditemukan**")
                for _, row in df_hasil_lensa.iterrows():
                    lensa_id = row["id"]
                    tipe = row["tipe"]
                    merk = row["merk"]
                    jenis = row["jenis"]
                    sph = row["sph"]
                    cyl = row["cyl"]
                    add_power = row.get("add_power", "")
                    stock = int(row["stock"] or 0)
                    harga_modal = int(row["harga_modal"] or 0)
                    harga_jual = int(row["harga_jual"] or 0)

                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{merk} — {tipe} {jenis}**")
                            st.markdown(f"SPH `{sph}` CYL `{cyl}` Add `{add_power}` | Stock: `{stock}` | Modal: `Rp {harga_modal:,}` | Jual: `Rp {harga_jual:,}`".replace(",", "."))
                        with col2:
                            if st.button("✏️ Edit", key=f"btn_edit_lensa_{lensa_id}"):
                                st.session_state["edit_lensa_id"] = lensa_id

                    if st.session_state.get("edit_lensa_id") == lensa_id:
                        with st.container(border=True):
                            st.markdown(f"**Edit — {merk} {tipe} {jenis} SPH {sph} CYL {cyl}**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                stock_baru = st.number_input("Stock", value=stock, min_value=0, key=f"stock_lensa_{lensa_id}")
                            with col2:
                                harga_modal_baru = st.number_input("Harga Modal", value=harga_modal, min_value=0, step=1000, key=f"modal_lensa_{lensa_id}")
                            with col3:
                                harga_jual_baru = st.number_input("Harga Jual", value=harga_jual, min_value=0, step=1000, key=f"jual_lensa_{lensa_id}")

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Simpan", key=f"simpan_lensa_{lensa_id}"):
                                    supabase = get_supabase()
                                    supabase.table("lensa").update({
                                        "stock": stock_baru,
                                        "harga_modal": harga_modal_baru,
                                        "harga_jual": harga_jual_baru
                                    }).eq("id", lensa_id).execute()

                                    keterangan = (
                                        f"Revisi: stock {stock}→{stock_baru}, "
                                        f"harga modal {harga_modal}→{harga_modal_baru}, "
                                        f"harga jual {harga_jual}→{harga_jual_baru}"
                                    )
                                    catat_log_lensa(tipe, merk, jenis, sph, cyl, add_power, "revisi", keterangan, user)

                                    st.success(f"Lensa {merk} {tipe} {jenis} SPH {sph} CYL {cyl} berhasil diupdate!")
                                    st.session_state.pop("edit_lensa_id", None)
                                    st.cache_data.clear()
                                    st.rerun()
                            with col_cancel:
                                if st.button("❌ Batal", key=f"batal_lensa_{lensa_id}"):
                                    st.session_state.pop("edit_lensa_id", None)
                                    st.rerun()