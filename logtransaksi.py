import streamlit as st
import pandas as pd
from utils import get_table_cached, get_table_raw, get_supabase


def run():
    st.title("📜 Data Transaksi Optik Maroon")

    # ==============================
    # Ambil Data
    # ==============================
    df_detail = get_table_cached("transaksi_detail")
    df_pembayaran = get_table_cached("pembayaran")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    if df_detail.empty:
        st.warning("Data transaksi belum tersedia.")
        return

    # Normalisasi kolom
    df_detail.columns = df_detail.columns.str.strip().str.lower().str.replace(' ', '_')
    df_pembayaran.columns = df_pembayaran.columns.str.strip().str.lower().str.replace(' ', '_')

    # ==============================
    # Ambil status terakhir pembayaran
    # ==============================
    if not df_pembayaran.empty and "pembayaran_ke" in df_pembayaran.columns:
        df_status = (
            df_pembayaran
            .sort_values(by='pembayaran_ke')
            .groupby('id_transaksi', as_index=False)
            .last()
        )[['id_transaksi', 'status']]
    else:
        df_status = pd.DataFrame(columns=['id_transaksi', 'status'])

    # Merge status ke detail
    df_ringkas = df_detail.merge(df_status, on='id_transaksi', how='left')

    # ==============================
    # Pilih Kolom
    # ==============================
    selected_cols = [
        'tanggal', 'id_transaksi', 'nama', 'merk_frame', 'kode_frame',
        'jenis_lensa', 'tipe_lensa', 'harga_frame', 'harga_lensa',
        'total_harga', 'status', 'user_name'
    ]
    df_ringkas = df_ringkas[[col for col in selected_cols if col in df_ringkas.columns]]

    # ==============================
    # Format tanggal + sort descending (terbaru di atas)
    # ==============================
    df_ringkas['tanggal'] = pd.to_datetime(df_ringkas['tanggal'], errors='coerce')
    df_ringkas = df_ringkas.dropna(subset=['tanggal'])
    df_ringkas = df_ringkas.sort_values('tanggal', ascending=False).reset_index(drop=True)
    df_ringkas['tahun'] = df_ringkas['tanggal'].dt.year
    df_ringkas['bulan_num'] = df_ringkas['tanggal'].dt.month
    df_ringkas['bulan_nama'] = df_ringkas['tanggal'].dt.strftime('%B')
    df_ringkas['tanggal'] = df_ringkas['tanggal'].dt.strftime('%d-%m-%Y')

    # ==============================
    # TAB: History vs Revisi
    # ==============================
    tab1, tab2 = st.tabs(["📋 History Transaksi", "✏️ Revisi Transaksi"])

    # ==============================
    # TAB 1: HISTORY
    # ==============================
    with tab1:
        col1, col2, col3 = st.columns(3)

        tahun_list = sorted(df_ringkas['tahun'].unique(), reverse=True)
        with col1:
            selected_tahun = st.selectbox("Pilih Tahun", tahun_list, key="ht_tahun")

        df_filtered = df_ringkas[df_ringkas['tahun'] == selected_tahun]

        bulan_tersedia = (
            df_filtered[['bulan_num', 'bulan_nama']]
            .drop_duplicates()
            .sort_values('bulan_num')
        )
        bulan_options = ["Semua"] + bulan_tersedia['bulan_nama'].tolist()

        with col2:
            selected_bulan = st.selectbox("Pilih Bulan", bulan_options, key="ht_bulan")

        if selected_bulan != "Semua":
            df_filtered = df_filtered[df_filtered['bulan_nama'] == selected_bulan]

        with col3:
            search_nama = st.text_input("🔍 Cari Nama", key="ht_nama")

        if search_nama:
            df_filtered = df_filtered[
                df_filtered['nama'].str.contains(search_nama, case=False, na=False)
            ]

        if not df_filtered.empty:
            df_display = df_filtered.drop(
                columns=['tahun', 'bulan_num', 'bulan_nama'], errors='ignore'
            ).reset_index(drop=True)
            df_display.index = df_display.index + 1
            df_display.index.name = "No"
            df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]
            st.dataframe(df_display, width='stretch')
        else:
            st.info("Tidak ada data ditemukan.")

    # ==============================
    # TAB 2: REVISI TRANSAKSI
    # ==============================
    with tab2:
        st.subheader("✏️ Revisi Transaksi")

        user = st.session_state.get("user", "Unknown")
        supabase = get_supabase()

        # ==============================
        # PILIH KASUS
        # ==============================
        kasus = st.selectbox("Pilih Jenis Revisi", [
            "1️⃣ Koreksi Salah Input Frame",
            "2️⃣ Frame Patah / Rusak",
            "3️⃣ Tukar Frame"
        ], key="revisi_kasus")

        st.divider()

        # ==============================
        # FILTER PENCARIAN TRANSAKSI
        # ==============================
        col1, col2 = st.columns(2)
        with col1:
            cari_nama = st.text_input("Cari Nama Pelanggan", placeholder="contoh: Steven", key="revisi_cari_nama")
        with col2:
            cari_id = st.text_input("Cari ID Transaksi", placeholder="contoh: OM/T/001", key="revisi_cari_id")

        df_cari = df_detail.copy()
        if cari_nama:
            df_cari = df_cari[df_cari["nama"].str.contains(cari_nama.strip(), case=False, na=False)]
        if cari_id:
            df_cari = df_cari[df_cari["id_transaksi"].str.contains(cari_id.strip(), case=False, na=False)]

        if not cari_nama and not cari_id:
            st.info("Masukkan nama atau ID transaksi untuk mencari.")
            return

        if df_cari.empty:
            st.warning("Transaksi tidak ditemukan.")
            return

        st.markdown(f"**{len(df_cari)} transaksi ditemukan**")

        # ==============================
        # DATA FRAMES UNTUK SELECTBOX
        # ==============================
        df_frames_raw = get_table_raw("frames")
        df_frames_raw.columns = df_frames_raw.columns.str.lower()

        # ==============================
        # TAMPILKAN HASIL PENCARIAN
        # ==============================
        for _, row in df_cari.iterrows():
            trx_id = row["id_transaksi"]
            nama = row["nama"]
            merk_frame = row.get("merk_frame", "")
            kode_frame = row.get("kode_frame", "")
            harga_frame = row.get("harga_frame", 0) or 0
            harga_lensa = row.get("harga_lensa", 0) or 0
            total_harga = row.get("total_harga", 0) or 0
            detail_id = row["id"]

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{nama}** — `{trx_id}`")
                    st.markdown(
                        f"Frame: `{merk_frame} {kode_frame}` | "
                        f"Harga Frame: `Rp {int(harga_frame):,}` | "
                        f"Total: `Rp {int(total_harga):,}`".replace(",", ".")
                    )
                with col2:
                    if st.button("✏️ Revisi", key=f"btn_revisi_{detail_id}"):
                        st.session_state["revisi_id"] = detail_id

            # ==============================
            # FORM REVISI
            # ==============================
            if st.session_state.get("revisi_id") == detail_id:

                with st.container(border=True):

                    # ==========================
                    # KASUS 1: KOREKSI SALAH INPUT
                    # ==========================
                    if kasus == "1️⃣ Koreksi Salah Input Frame":
                        st.markdown(f"**Koreksi Salah Input — {nama} | {trx_id}**")
                        st.markdown(f"Frame saat ini: `{merk_frame} — {kode_frame}`")

                        merk_options = sorted(df_frames_raw["merk"].dropna().unique().tolist())

                        col1, col2 = st.columns(2)
                        with col1:
                            merk_baru = st.selectbox(
                                "Merk Frame yang Benar",
                                options=merk_options,
                                index=merk_options.index(merk_frame) if merk_frame in merk_options else 0,
                                key=f"koreksi_merk_{detail_id}"
                            )

                        df_kode_filtered = df_frames_raw[df_frames_raw["merk"] == merk_baru]
                        kode_options = sorted(df_kode_filtered["kode"].dropna().unique().tolist())

                        with col2:
                            kode_baru = st.selectbox(
                                "Kode Frame yang Benar",
                                options=kode_options,
                                index=kode_options.index(kode_frame) if kode_frame in kode_options else 0,
                                key=f"koreksi_kode_{detail_id}"
                            )

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Simpan", key=f"simpan_koreksi_{detail_id}"):

                                # Update transaksi_detail
                                supabase.table("transaksi_detail").update({
                                    "merk_frame": merk_baru,
                                    "kode_frame": kode_baru
                                }).eq("id", detail_id).execute()

                                # Kembalikan stock frame lama (+1)
                                row_lama = df_frames_raw[
                                    (df_frames_raw["merk"] == merk_frame) &
                                    (df_frames_raw["kode"] == kode_frame)
                                ]
                                if not row_lama.empty:
                                    id_lama = int(row_lama["id"].values[0])
                                    stock_lama_val = int(row_lama["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_lama_val + 1
                                    }).eq("id", id_lama).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_frame,
                                        "kode": kode_frame,
                                        "status": "koreksi",
                                        "keterangan": f"Koreksi salah input transaksi {trx_id}, nama: {nama}. Frame dikembalikan ke stock, stock {stock_lama_val}→{stock_lama_val + 1}",
                                        "user_name": user
                                    }).execute()

                                # Kurangi stock frame yang benar (-1)
                                row_baru = df_frames_raw[
                                    (df_frames_raw["merk"] == merk_baru) &
                                    (df_frames_raw["kode"] == kode_baru)
                                ]
                                if not row_baru.empty:
                                    id_baru = int(row_baru["id"].values[0])
                                    stock_baru_val = int(row_baru["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_baru_val - 1
                                    }).eq("id", id_baru).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_baru,
                                        "kode": kode_baru,
                                        "status": "koreksi",
                                        "keterangan": f"Koreksi salah input transaksi {trx_id}, nama: {nama}. Frame yang benar dikeluarkan, stock {stock_baru_val}→{stock_baru_val - 1}",
                                        "user_name": user
                                    }).execute()

                                st.success(f"Koreksi berhasil! {merk_frame} {kode_frame} → {merk_baru} {kode_baru}")
                                st.session_state.pop("revisi_id", None)
                                st.cache_data.clear()
                                st.rerun()

                        with col_cancel:
                            if st.button("❌ Batal", key=f"batal_koreksi_{detail_id}"):
                                st.session_state.pop("revisi_id", None)
                                st.rerun()

                    # ==========================
                    # KASUS 2: FRAME PATAH
                    # ==========================
                    elif kasus == "2️⃣ Frame Patah / Rusak":
                        st.markdown(f"**Frame Patah — {nama} | {trx_id}**")
                        st.markdown(f"Frame rusak: `{merk_frame} — {kode_frame}`")
                        st.caption("Stock frame rusak dikurangi 1, stock frame pengganti juga dikurangi 1.")

                        merk_options = sorted(df_frames_raw["merk"].dropna().unique().tolist())

                        col1, col2 = st.columns(2)
                        with col1:
                            merk_pengganti = st.selectbox(
                                "Merk Frame Pengganti",
                                options=merk_options,
                                index=merk_options.index(merk_frame) if merk_frame in merk_options else 0,
                                key=f"patah_merk_{detail_id}"
                            )

                        df_kode_pengganti = df_frames_raw[df_frames_raw["merk"] == merk_pengganti]
                        kode_options_pengganti = sorted(df_kode_pengganti["kode"].dropna().unique().tolist())

                        with col2:
                            kode_pengganti = st.selectbox(
                                "Kode Frame Pengganti",
                                options=kode_options_pengganti,
                                index=kode_options_pengganti.index(kode_frame) if kode_frame in kode_options_pengganti else 0,
                                key=f"patah_kode_{detail_id}"
                            )

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Simpan", key=f"simpan_patah_{detail_id}"):

                                # Kurangi stock frame rusak (-1)
                                row_rusak = df_frames_raw[
                                    (df_frames_raw["merk"] == merk_frame) &
                                    (df_frames_raw["kode"] == kode_frame)
                                ]
                                if not row_rusak.empty:
                                    id_rusak = int(row_rusak["id"].values[0])
                                    stock_rusak = int(row_rusak["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_rusak - 1
                                    }).eq("id", id_rusak).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_frame,
                                        "kode": kode_frame,
                                        "status": "rusak",
                                        "keterangan": f"Frame rusak/patah dalam transaksi {trx_id}, nama: {nama}. Stock {stock_rusak}→{stock_rusak - 1}",
                                        "user_name": user
                                    }).execute()

                                # Kurangi stock frame pengganti (-1)
                                row_pgn = df_frames_raw[
                                    (df_frames_raw["merk"] == merk_pengganti) &
                                    (df_frames_raw["kode"] == kode_pengganti)
                                ]
                                if not row_pgn.empty:
                                    id_pgn = int(row_pgn["id"].values[0])
                                    stock_pgn = int(row_pgn["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_pgn - 1
                                    }).eq("id", id_pgn).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_pengganti,
                                        "kode": kode_pengganti,
                                        "status": "pengganti",
                                        "keterangan": f"Frame pengganti transaksi {trx_id}, nama: {nama} (frame {merk_frame} {kode_frame} rusak). Stock {stock_pgn}→{stock_pgn - 1}",
                                        "user_name": user
                                    }).execute()

                                # Update transaksi_detail dengan frame pengganti
                                supabase.table("transaksi_detail").update({
                                    "merk_frame": merk_pengganti,
                                    "kode_frame": kode_pengganti
                                }).eq("id", detail_id).execute()

                                st.success(f"Frame {merk_frame} {kode_frame} dicatat rusak. Pengganti: {merk_pengganti} {kode_pengganti}")
                                st.session_state.pop("revisi_id", None)
                                st.cache_data.clear()
                                st.rerun()

                        with col_cancel:
                            if st.button("❌ Batal", key=f"batal_patah_{detail_id}"):
                                st.session_state.pop("revisi_id", None)
                                st.rerun()

                    # ==========================
                    # KASUS 3: TUKAR FRAME
                    # ==========================
                    elif kasus == "3️⃣ Tukar Frame":
                        st.markdown(f"**Tukar Frame — {nama} | {trx_id}**")
                        st.markdown(
                            f"Frame saat ini: `{merk_frame} — {kode_frame}` | "
                            f"Harga: `Rp {int(harga_frame):,}`".replace(",", ".")
                        )

                        merk_options = sorted(df_frames_raw["merk"].dropna().unique().tolist())

                        col1, col2 = st.columns(2)
                        with col1:
                            merk_tukar = st.selectbox(
                                "Merk Frame Baru",
                                options=merk_options,
                                index=merk_options.index(merk_frame) if merk_frame in merk_options else 0,
                                key=f"tukar_merk_{detail_id}"
                            )

                        df_kode_tukar = df_frames_raw[df_frames_raw["merk"] == merk_tukar]
                        kode_options_tukar = sorted(df_kode_tukar["kode"].dropna().unique().tolist())

                        with col2:
                            kode_tukar = st.selectbox(
                                "Kode Frame Baru",
                                options=kode_options_tukar,
                                index=kode_options_tukar.index(kode_frame) if kode_frame in kode_options_tukar else 0,
                                key=f"tukar_kode_{detail_id}"
                            )

                        # Ambil harga frame baru otomatis dari tabel frames
                        row_tukar = df_frames_raw[
                            (df_frames_raw["merk"] == merk_tukar) &
                            (df_frames_raw["kode"] == kode_tukar)
                        ]
                        harga_frame_baru = int(row_tukar["harga_jual"].values[0]) if not row_tukar.empty else int(harga_frame)

                        st.markdown(f"Harga frame baru: `Rp {harga_frame_baru:,}`".replace(",", "."))

                        pinalti = st.number_input(
                            "Biaya Pinalti / Tambahan",
                            value=0,
                            min_value=0,
                            step=1000,
                            key=f"tukar_pinalti_{detail_id}"
                        )

                        # Hitung total baru
                        total_baru = int(harga_lensa) + harga_frame_baru + pinalti
                        selisih = total_baru - int(total_harga)

                        st.markdown(
                            f"Total lama: `Rp {int(total_harga):,}` → "
                            f"Total baru: `Rp {total_baru:,}`".replace(",", ".")
                        )
                        if selisih < 0:
                            st.caption(f"💸 Harga turun, kembalikan Rp {abs(selisih):,} ke pelanggan (tidak dicatat).".replace(",", "."))
                        elif selisih > 0:
                            st.caption(f"💰 Harga naik, pelanggan perlu bayar selisih Rp {selisih:,}.".replace(",", "."))
                        else:
                            st.caption("✅ Harga sama, tidak ada selisih.")

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Simpan", key=f"simpan_tukar_{detail_id}"):

                                # Kembalikan stock frame lama (+1)
                                row_lama = df_frames_raw[
                                    (df_frames_raw["merk"] == merk_frame) &
                                    (df_frames_raw["kode"] == kode_frame)
                                ]
                                if not row_lama.empty:
                                    id_lama = int(row_lama["id"].values[0])
                                    stock_lama_v = int(row_lama["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_lama_v + 1
                                    }).eq("id", id_lama).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_frame,
                                        "kode": kode_frame,
                                        "status": "tukar",
                                        "keterangan": f"Frame dikembalikan karena tukar dalam transaksi {trx_id}, nama: {nama}. Stock {stock_lama_v}→{stock_lama_v + 1}",
                                        "user_name": user
                                    }).execute()

                                # Kurangi stock frame baru (-1)
                                if not row_tukar.empty:
                                    id_tukar = int(row_tukar["id"].values[0])
                                    stock_tukar_v = int(row_tukar["stock"].values[0] or 0)
                                    supabase.table("frames").update({
                                        "stock": stock_tukar_v - 1
                                    }).eq("id", id_tukar).execute()
                                    supabase.table("log_frames").insert({
                                        "timestamp_log": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "merk": merk_tukar,
                                        "kode": kode_tukar,
                                        "status": "tukar",
                                        "keterangan": f"Frame pengganti tukar dalam transaksi {trx_id}, nama: {nama}. Stock {stock_tukar_v}→{stock_tukar_v - 1}",
                                        "user_name": user
                                    }).execute()

                                # Update transaksi_detail
                                supabase.table("transaksi_detail").update({
                                    "merk_frame": merk_tukar,
                                    "kode_frame": kode_tukar,
                                    "harga_frame": harga_frame_baru,
                                    "tambahan": pinalti,
                                    "total_harga": total_baru
                                }).eq("id", detail_id).execute()

                                # Update transaksi
                                supabase.table("transaksi").update({
                                    "total_harga": total_baru
                                }).eq("id_transaksi", trx_id).execute()

                                # Update pembayaran — ambil data fresh
                                df_pemb = get_table_raw("pembayaran")
                                df_pemb.columns = df_pemb.columns.str.lower()
                                df_pemb_trx = df_pemb[df_pemb["id_transaksi"] == trx_id]

                                if not df_pemb_trx.empty:
                                    total_dibayar = int(df_pemb_trx["nominal_pembayaran"].sum())
                                    sisa_baru = max(0, total_baru - total_dibayar)
                                    status_baru = "lunas" if sisa_baru == 0 else "belum lunas"

                                    last_pemb = df_pemb_trx.sort_values("pembayaran_ke").iloc[-1]
                                    supabase.table("pembayaran").update({
                                        "total_harga": total_baru,
                                        "sisa": sisa_baru,
                                        "status": status_baru
                                    }).eq("id", int(last_pemb["id"])).execute()

                                st.success(
                                    f"Tukar frame berhasil! {merk_frame} {kode_frame} → {merk_tukar} {kode_tukar}. "
                                    f"Total baru: Rp {total_baru:,}".replace(",", ".")
                                )
                                st.session_state.pop("revisi_id", None)
                                st.cache_data.clear()
                                st.rerun()

                        with col_cancel:
                            if st.button("❌ Batal", key=f"batal_tukar_{detail_id}"):
                                st.session_state.pop("revisi_id", None)
                                st.rerun()