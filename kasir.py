import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    get_table_cached, insert_row_supabase, get_supabase, 
    generate_id_pembayaran_supabase, generate_id_transaksi_supabase, 
    get_or_create_pelanggan_id_supabase, cari_harga_lensa_luar, cari_harga_lensa_stock, 
    catat_logframe_supabase, catat_loglensa_supabase
    )

@st.dialog("✅ Pembayaran Berhasil")
def dialog_ringkasan_kasir(data, reset_func):
    st.markdown(f"""
    **Tanggal Transaksi:** {data['tanggal']}  
    **ID Transaksi:** `{data['id_transaksi']}`  
    **Nama:** {data['nama']}  
    **Status:** {data['status']}  
    **Sisa:** Rp {data['sisa']:,.0f}
    """)
    if st.button("OK"):
        reset_func()
        st.rerun()
        
def run():
    @st.cache_data(ttl=60)
    def load_data():
        df_frame = get_table_cached("frames")
        df_lensa_stock = get_table_cached("lensa")
        df_lensa_luar = get_table_cached("lensa_luar_stock")

        return df_frame, df_lensa_stock, df_lensa_luar

    df_frame, df_lensa_stock, df_lensa_luar = load_data()
    
    df_frame.columns = df_frame.columns.str.lower()
    df_lensa_stock.columns = df_lensa_stock.columns.str.lower()
    df_lensa_luar.columns = df_lensa_luar.columns.str.lower()
    
    def format_2digit(val):
        try:
            return f"{float(val):.2f}"
        except Exception:
            return str(val).strip() if val is not None else ""
        
    df_lensa_stock['sph'] = df_lensa_stock['sph'].apply(format_2digit)
    df_lensa_stock['cyl'] = df_lensa_stock['cyl'].apply(format_2digit)
    df_lensa_stock['add_power'] = df_lensa_stock['add_power'].apply(format_2digit)
    for col in ['jenis', 'tipe', 'merk']:
        df_lensa_stock[col] = df_lensa_stock[col].astype(str).str.strip()
    

    st.title("🧾 Transaksi Kasir")
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y, %H:%M:%S")
    tanggal_transaksi = st.date_input("📅 Tanggal Transaksi", value=date.today(), format="DD/MM/YYYY")
    tanggal_str = tanggal_transaksi.strftime("%d-%m-%Y")

    nama = st.text_input("Nama Konsumen", key="nama_konsumen")
    kontak = st.text_input("No HP", key="no_hp")
    if not nama or not kontak:
        st.warning("Nama dan No HP harus diisi.")
        st.stop()


    nama = str(nama).strip().lower()
    kontak = str(kontak).strip()

    if "daftar_item" not in st.session_state:
        st.session_state.daftar_item = []

    st.subheader("➕ Tambah Item")
    status_frame = st.selectbox("Status Frame", ["Stock", "Punya Sendiri"])
    if status_frame == "Stock":
        merk_options = [""] + sorted(df_frame['merk'].dropna().unique())
        merk_frame = st.selectbox("Merk Frame", merk_options, format_func=lambda x: "-- Pilih Merk --" if x == "" else x)
        if merk_frame:
            kode_options = [""] + sorted(df_frame[df_frame['merk'] == merk_frame]['kode'].dropna().unique())
        else:
            kode_options = [""]            
        kode_frame = st.selectbox("Kode Frame", kode_options, format_func=lambda x: "-- Pilih Kode --" if x == "" else x)

        if not merk_frame or not kode_frame:
            st.warning("Merk dan Kode Frame harus dipilih.")
            st.stop()
    else:
        merk_frame, kode_frame = "", ""
        
    status_lensa = st.selectbox("Status Lensa", ["Stock", "Inti", "Pesan", "Overlens"])
    if status_lensa == "Stock":
        df_lensa = df_lensa_stock.copy()
        # Tipe Lensa
        tipe_option = sorted(df_lensa['tipe'].dropna().unique())
        tipe_lensa = st.selectbox("Tipe Lensa", tipe_option)
        # Merk Lensa
        df_merk = df_lensa[df_lensa['tipe'] == tipe_lensa]
        merk_option = sorted(df_merk['merk'].dropna().unique())
        merk_lensa = st.selectbox("Merk Lensa", merk_option)
        # Jenis Lensa
        df_jenis = df_lensa[(df_lensa['tipe'] == tipe_lensa) & (df_lensa['merk'] == merk_lensa)]
        jenis_option = sorted(df_jenis['jenis'].dropna().unique())
        jenis_lensa = st.selectbox("Jenis Lensa", jenis_option)
    else:
        df_lensa = df_lensa_luar[df_lensa_luar['status'] == status_lensa].copy()
        # Tipe Lensa
        tipe_option = sorted(df_lensa['tipe'].dropna().unique())
        tipe_lensa = st.selectbox("Tipe Lensa", tipe_option)
        # Merk Lensa
        df_merk = df_lensa[df_lensa['tipe'] == tipe_lensa]
        merk_option = sorted(df_merk['merk'].dropna().unique())
        merk_lensa = st.selectbox("Merk Lensa", merk_option)
        # Jenis Lensa
        df_jenis = df_lensa[(df_lensa['tipe'] == tipe_lensa) & (df_lensa['merk'] == merk_lensa)]
        jenis_option = sorted(df_jenis['jenis'].dropna().unique())
        jenis_lensa = st.selectbox("Jenis Lensa", jenis_option)
    # Nama Lensa hanya untuk non-stock
    nama_lensa = ""
    if status_lensa == "Stock":
        st.markdown("**Ukuran Lensa**")     
        colR, colL = st.columns(2)
        # List Ukuran
        sph_list = sorted(df_lensa['sph'].dropna().unique())
        cyl_list = sorted(df_lensa['cyl'].dropna().unique())
        add_list = sorted(df_lensa['add_power'].dropna().unique())

        with colR:
            sph_r = st.selectbox("SPH R", sph_list, index = sph_list.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_list, index = cyl_list.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else None
            add_r = st.selectbox("Add R", sorted(df_lensa['add_power'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else None
        with colL:
            sph_l = st.selectbox("SPH L", sph_list, index = sph_list.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_list, index = cyl_list.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else None
            add_l = st.selectbox("Add L", sorted(df_lensa['add_power'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else None
    
    else:
        df_lensa.columns = df_lensa.columns.str.lower().str.strip().str.replace(" ", "_")
        nama_lensa = st.selectbox("Nama Lensa", sorted(df_lensa[
            (df_lensa['jenis'] == jenis_lensa) & 
            (df_lensa['tipe'] == tipe_lensa) & 
            (df_lensa['merk'] == merk_lensa)
        ]['nama_lensa'].dropna().unique()))
                
        st.markdown("**Ukuran Lensa**")
        colR, colL = st.columns(2)
        # Range Ukuran
        sph_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-40, 41)]]
        cyl_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(-20, 1)]]
        add_range = [f"{x:.2f}" for x in [i * 0.25 for i in range(0, 13)]]

        with colR:
            sph_r = st.selectbox("SPH R", sph_range, index=sph_range.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_range, index=cyl_range.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else None
            add_r = st.selectbox("Add R", add_range) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""

        with colL:
            sph_l = st.selectbox("SPH L", sph_range, index=sph_range.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_range, index=cyl_range.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else None
            add_l = st.selectbox("Add L", add_range) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""


    # Konversi nilai add (pakai add_r, diasumsikan sama untuk L dan R)
    add_dipakai = add_r if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else None
    if status_lensa == "Stock":
        harga_lensa = cari_harga_lensa_stock(
            df_lensa, tipe_lensa, jenis_lensa, merk_lensa,
            float(sph_r), float(cyl_r), 
            float(add_dipakai) if add_dipakai is not None else None,
            pakai_reseller=False
        )
        if harga_lensa is None:
            st.warning("⚠️ Harga lensa stock tidak ditemukan!")
            st.stop()

    else:
        harga_lensa = cari_harga_lensa_luar(df_lensa, tipe_lensa, jenis_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, False)
        if harga_lensa is None:
            st.warning("⚠️ Ukuran tidak sesuai rentang harga manapun!")
            st.stop()

    tambahan = st.number_input("Biaya Tambahan (Rp)", min_value=0, step=5000, value=0)
    
    st.markdown("**Pilih Diskon**")
    diskon_mode = st.radio("Jenis Diskon", ["Diskon Persen", "Diskon Harga"])

    if diskon_mode == "Diskon Persen":
        diskon_persen = st.selectbox("Diskon (%)", [0, 5, 10, 15, 20])
        diskon_harga = 0
    else:
        diskon_persen = 0
        diskon_harga = st.number_input("Diskon Harga (Rp)", min_value=0, step=500, value=0)

    # Harga Frame
    if status_frame == "Stock":
        harga_frame = df_frame[(df_frame['merk'] == merk_frame) & (df_frame['kode'] == kode_frame)]['harga_jual'].values[0]
    else:
        harga_frame = 0
    # Diskon
    harga_frame = int(harga_frame or 0)
    tambahan = int(tambahan or 0)
        
    if diskon_mode == "Diskon Persen":
        diskon_nilai = float((harga_frame + harga_lensa + tambahan) * (diskon_persen / 100))
    else:
        diskon_nilai = diskon_harga
    diskon_nilai = int(diskon_nilai or 0)
    # Total Harga Setelah Diskon
    harga_setelah_diskon = harga_frame + harga_lensa + tambahan - diskon_nilai

    # Ringkasan Harga
    st.markdown(f"##### Harga Frame: Rp {harga_frame:,.0f}")
    st.markdown(f"##### Harga lensa: Rp {harga_lensa:,.0f}")

    if st.button("📝 Tambah ke Daftar"):
    # ===================== CEK SEMUA STOK DULU =====================
        # --- Cek stok frame ---
        if status_frame == "Stock":
            kondisi = (
                (df_frame['merk'] == merk_frame) &
                (df_frame['kode'] == kode_frame)
            )
            if kondisi.any():
                idx = kondisi.idxmax()
                stock_lama = int(str(df_frame.at[idx, 'stock']).replace(",", "").strip())
                if stock_lama == 0:
                    st.warning(f"Stock frame {merk_frame} {kode_frame} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
        # --- Cek stok lensa kanan ---
        if status_lensa == "Stock":
            if tipe_lensa.lower() == 'single vision':
                kondisi_kanan = (
                    (df_lensa_stock['jenis'] == jenis_lensa) &
                    (df_lensa_stock['tipe'] == tipe_lensa) &
                    (df_lensa_stock['merk'] == merk_lensa) &
                    (df_lensa_stock['sph'] == sph_r) &
                    (df_lensa_stock['cyl'] == cyl_r)
                )
            else:
                kondisi_kanan = (
                    (df_lensa_stock['jenis'] == jenis_lensa) &
                    (df_lensa_stock['tipe'] == tipe_lensa) &
                    (df_lensa_stock['merk'] == merk_lensa) &
                    (df_lensa_stock['sph'] == sph_r) &
                    (df_lensa_stock['cyl'] == cyl_r) &
                    (df_lensa_stock['add_power'] == add_r) if add_r is not None else (df_lensa_stock['add_power'].isna())
                )
            if kondisi_kanan.any():
                idx = kondisi_kanan.idxmax()
                stock_val = df_lensa_stock.at[idx, 'stock']
                try:
                    stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                except Exception:
                    stock_lama = 0
                if stock_lama == 0:
                    st.warning(f"Stock lensa {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph_r} CYL {cyl_r} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
        # --- Cek stok lensa kiri ---
        if status_lensa == "Stock":
            if tipe_lensa.lower() == 'single vision':
                kondisi_kiri = (
                    (df_lensa_stock['jenis'] == jenis_lensa) &
                    (df_lensa_stock['tipe'] == tipe_lensa) &
                    (df_lensa_stock['merk'] == merk_lensa) &
                    (df_lensa_stock['sph'] == sph_l) &
                    (df_lensa_stock['cyl'] == cyl_l)
                )
            else:
                kondisi_kiri = (
                    (df_lensa_stock['jenis'] == jenis_lensa) &
                    (df_lensa_stock['tipe'] == tipe_lensa) &
                    (df_lensa_stock['merk'] == merk_lensa) &
                    (df_lensa_stock['sph'] == sph_l) &
                    (df_lensa_stock['cyl'] == cyl_l) &
                    (df_lensa_stock['add_power'] == add_l)
                )
            if kondisi_kiri.any():
                idx = kondisi_kiri.idxmax()
                stock_val = df_lensa_stock.at[idx, 'stock']
                try:
                    stock_lama = int(str(stock_val).replace(",", "").strip()) if str(stock_val).strip() else 0
                except Exception:
                    stock_lama = 0
                if stock_lama == 0:
                    st.warning(f"Stock lensa {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph_l} CYL {cyl_l} sudah habis!")
                    st.session_state['simpan_pembayaran'] = False
                    st.stop()
                        
        st.session_state.daftar_item.append({
            "status_frame": status_frame,
            "merk_frame": merk_frame,
            "kode_frame": kode_frame,
            "status_lensa": status_lensa,
            "jenis_lensa": jenis_lensa,
            "tipe_lensa": tipe_lensa,
            "merk_lensa": merk_lensa,
            "nama_lensa": nama_lensa,
            "sph_r": sph_r, "cyl_r": cyl_r, "axis_r": axis_r, "add_r": add_r,
            "sph_l": sph_l, "cyl_l": cyl_l, "axis_l": axis_l, "add_l": add_l,
            "harga_frame": harga_frame,
            "harga_lensa": harga_lensa,
            "tambahan": tambahan,
            "diskon": diskon_nilai,
            "subtotal": harga_setelah_diskon
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item:
        st.subheader("📋 Daftar Item")
        df = pd.DataFrame(st.session_state.daftar_item)

        # Tombol hapus
        for i, item in enumerate(st.session_state.daftar_item):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** Frame {item['merk_frame']} | Lensa {item['merk_lensa']} ({item['jenis_lensa']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item.pop(i)
                    st.rerun()

        df = pd.DataFrame(st.session_state.daftar_item)
        total = df['subtotal'].sum()
        
        df_display = df.copy()

        kolom_rupiah = ["harga_frame", "harga_lensa", "tambahan", "diskon", "subtotal"]

        for col in kolom_rupiah:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: f"Rp {int(x):,}".replace(",", ".") if pd.notnull(x) else "Rp 0"
                )

        st.dataframe(df_display, use_container_width=True)

        # Hitung total dan pembulatan
        total = sum([item['subtotal'] for item in st.session_state.daftar_item])
        ribuan_digit = (total // 1000) % 10
        dasar = (total // 10000) * 10000
        harga_final = dasar + 5000 if ribuan_digit >= 5 else dasar
        pembulatan = harga_final - total
                
        st.markdown(f"##### Harga: Rp {total:,.0f}")
        st.markdown(f"##### Pembulatan: Rp {pembulatan:,.0f}")
        st.markdown(f"#### 💰 Total Harga: Rp {harga_final:,.0f}")

        via = st.selectbox("Via Pembayaran", ["Cash", "Qris EDC Mandiri", "Qris EDC BCA", "Qris Statis Mandiri", "TF BCA", "TF Mandiri"])
        nominal = st.number_input("Masukkan Nominal", min_value=0, step=1000)
        sisa = harga_final - nominal
        if sisa <= 0:
            status = "Lunas"
            sisa = 0
        else:
            status = "Belum Lunas"
            
        metode = "Full" if status == "Lunas" else "Angsuran"

        if st.button("💾 Simpan Pembayaran"):
            st.session_state['id_pelanggan'] = get_or_create_pelanggan_id_supabase(nama, kontak)
            st.session_state['simpan_pembayaran'] = True
            
    # ===================== JIKA SEMUA STOK AMAN, LANJUTKAN =====================
    if st.session_state.get('simpan_pembayaran', False):
        id_pelanggan = st.session_state.get("id_pelanggan")
        id_transaksi = generate_id_transaksi_supabase(tanggal_transaksi)
        id_pembayaran = generate_id_pembayaran_supabase(datetime.now())
        user = st.session_state.get("user", "Unknown")

        # ==============================
        # HITUNG SUBTOTAL SETELAH PEMBULATAN
        # ==============================
        for i, item in enumerate(st.session_state.daftar_item):
            subtotal = item['subtotal']
            if i == len(st.session_state.daftar_item) - 1:
                subtotal += pembulatan
            item['subtotal_setelah_pembulatan'] = subtotal

        # ==============================
        # INSERT HEADER TRANSAKSI
        # ==============================
        insert_row_supabase("transaksi", {
            "id_transaksi": id_transaksi,
            "tanggal": tanggal_transaksi,
            "id_pelanggan": id_pelanggan,
            "nama": nama,
            "total_harga": harga_final,
            "user_name": user
        })

        # ==============================
        # INSERT DETAIL + UPDATE STOCK + LOG
        # ==============================
        supabase = get_supabase()

        for item in st.session_state.daftar_item:

            # INSERT DETAIL
            insert_row_supabase("transaksi_detail", {
                "timestamp_log": datetime.now().replace(microsecond=0),
                "tanggal": tanggal_transaksi,
                "id_transaksi": id_transaksi,
                "id_pelanggan": id_pelanggan,
                "nama": nama,
                "status_frame": item['status_frame'],
                "merk_frame": item['merk_frame'],
                "kode_frame": item['kode_frame'],
                "status_lensa": item['status_lensa'],
                "jenis_lensa": item['jenis_lensa'],
                "tipe_lensa": item['tipe_lensa'],
                "merk_lensa": item['merk_lensa'],
                "nama_lensa": item['nama_lensa'],
                "sph_r": item['sph_r'],
                "cyl_r": item['cyl_r'],
                "axis_r": item['axis_r'],
                "add_r": item['add_r'],
                "sph_l": item['sph_l'],
                "cyl_l": item['cyl_l'],
                "axis_l": item['axis_l'],
                "add_l": item['add_l'],
                "harga_frame": item['harga_frame'],
                "harga_lensa": item['harga_lensa'],
                "tambahan": item['tambahan'],
                "diskon": item['diskon'],
                "subtotal": item['subtotal'],
                "total_harga": item['subtotal_setelah_pembulatan'],
                "user_name": user
            })

            # ==========================
            # UPDATE STOCK FRAME
            # ==========================
            if item['status_frame'] == "Stock":
                frame = supabase.table("frames") \
                    .select("stock") \
                    .eq("merk", item['merk_frame']) \
                    .eq("kode", item['kode_frame']) \
                    .execute()

                if frame.data:
                    stock_lama = frame.data[0]["stock"] or 0
                    stock_baru = max(0, stock_lama - 1)

                    supabase.table("frames") \
                        .update({"stock": stock_baru}) \
                        .eq("merk", item['merk_frame']) \
                        .eq("kode", item['kode_frame']) \
                        .execute()

                    catat_logframe_supabase(
                        item['merk_frame'],
                        item['kode_frame'],
                        "kasir",
                        status_frame=item['status_frame'],
                        id_transaksi=id_transaksi,
                        nama=nama,
                        user=user
                    )
                                        
            # Update stok lensa
            if item['status_lensa'] == "Stock":

                for side in ["r", "l"]:
                    sph = item[f"sph_{side}"]
                    cyl = item[f"cyl_{side}"]
                    add = item[f"add_{side}"]

                    # Ambil data dulu
                    query = supabase.table("lensa") \
                        .select("stock") \
                        .eq("tipe", item['tipe_lensa']) \
                        .eq("jenis", item['jenis_lensa']) \
                        .eq("merk", item['merk_lensa']) \
                        .eq("sph", sph) \
                        .eq("cyl", cyl)

                    if add:
                        query = query.eq("add_power", add)
                    else:
                        query = query.is_("add_power", None)

                    lensa = query.execute()

                    if lensa.data:
                        stock_lama = lensa.data[0]["stock"] or 0
                        stock_baru = max(0, stock_lama - 1)

                        # 🔥 UPDATE QUERY TERPISAH
                        update_query = supabase.table("lensa") \
                            .update({"stock": stock_baru}) \
                            .eq("tipe", item['tipe_lensa']) \
                            .eq("jenis", item['jenis_lensa']) \
                            .eq("merk", item['merk_lensa']) \
                            .eq("sph", sph) \
                            .eq("cyl", cyl)

                        if add:
                            update_query = update_query.eq("add_power", add)
                        else:
                            update_query = update_query.is_("add_power", None)

                        update_query.execute()

                        # Log
                        catat_loglensa_supabase(
                            jenis=item['jenis_lensa'],
                            tipe=item['tipe_lensa'],
                            merk=item['merk_lensa'],
                            sph=sph,
                            cyl=cyl,
                            add_power=add,
                            source="kasir",
                            status_lensa=item['status_lensa'],
                            id_transaksi=id_transaksi,
                            nama=nama,
                            user=user
                        )

        # Simpan pembayaran
        existing = supabase.table("pembayaran") \
            .select("id") \
            .eq("id_transaksi", id_transaksi) \
            .execute()

        pembayaran_ke = 1        
        
        tanggal_bayar = tanggal_str

        insert_row_supabase("pembayaran", {
            "timestamp_log": datetime.now().replace(microsecond=0),
            "id_transaksi": id_transaksi,
            "id_pembayaran": id_pembayaran,
            "id_pelanggan": id_pelanggan,
            "tanggal": tanggal_transaksi,
            "tanggal_bayar": tanggal_transaksi,
            "nama": nama,
            "no_hp": kontak,
            "metode": metode,
            "via": via,
            "total_harga": harga_final,
            "nominal_pembayaran": nominal,
            "sisa": sisa,
            "status": status,
            "pembayaran_ke": pembayaran_ke,
            "user_name": user
        })

        st.session_state['ringkasan_tersimpan'] = {
            'id_transaksi': id_transaksi,
            'tanggal': today,
            'nama': nama.title(),
            'status': status,
            'sisa': sisa
        }

        st.session_state['simpan_pembayaran'] = False
        st.rerun()

    def reset_form_kasir():
        st.session_state.pop("daftar_item", None)
        st.session_state.pop("simpan_pembayaran", None)
        st.session_state.pop("ringkasan_tersimpan", None)
        st.session_state.pop("nama_konsumen", None)
        st.session_state.pop("no_hp", None)

    if 'ringkasan_tersimpan' in st.session_state:
        dialog_ringkasan_kasir(st.session_state['ringkasan_tersimpan'], reset_form_kasir)