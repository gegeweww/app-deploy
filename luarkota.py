def run():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from utils import append_row, cari_harga_lensa_luar, get_dataframe
    from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES
    

    df_lensa_luar = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES["lensa_luar_stock"])
    df_lensa_luar.columns = df_lensa_luar.columns.str.lower().str.replace(" ", "_")

    st.title("📦 Form Pesanan Luar Kota")

    if "daftar_item_luar" not in st.session_state:
        st.session_state.daftar_item_luar = []

    # Form input umum
    col1, col2 = st.columns(2)
    with col1:
        tanggal_ambil = st.date_input("📅 Tanggal Ambil Paket", value=datetime.today()).strftime('%Y-%m-%d')
    with col2:
        nama = st.selectbox("🧍 Nama", ["Rahmat", "Nelly"])

    # Form input item
    with st.form(key="form_item_luar"):
        st.subheader("➕ Tambah Item Lensa")
        col1, col2 = st.columns(2)
        with col1:
            status_lensa = st.selectbox("📌 Status Lensa", ["Stock", "Inti", "Pesan", "Overlens"])
            jenis = st.text_input("Jenis Lensa")
            tipe = st.text_input("Tipe Lensa")
            merk = st.text_input("Merk Lensa")
            nama_lensa = st.text_input("Nama Lensa")
            harga_lensa = st.number_input("💰 Harga Lensa (sebelum diskon)", min_value=0.0, step=1000.0)
        with col2:
            keterangan = st.text_area("📝 Keterangan Tambahan")
            ongkir = st.selectbox("🛵 Ongkos Bensin", [25000])
            potong = st.selectbox("✂️ Ongkos Potong", [17000, 27000, 32000])
            status_kirim = st.selectbox("📦 Status Kirim", ["Belum Dikirim", "Sudah Dikirim"])
            tanggal_kirim = "-"
            if status_kirim == "Sudah Dikirim":
                tanggal_kirim = st.date_input("📅 Tanggal Kirim", value=datetime.today()).strftime('%Y-%m-%d')

        # Ukuran lensa
        if status_lensa == "Stock":
            st.markdown("### 🔍 Ukuran R / L (Stock)")
            colR, colL = st.columns(2)
            with colR:
                sph_r = st.selectbox("SPH R", [f"{x:.2f}" for x in [i * 0.25 for i in range(-24, 24)]])
                cyl_r = st.selectbox("CYL R", [f"{x:.2f}" for x in [i * 0.25 for i in range(-8,1)]])
                axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
                add_r = st.text_input("Add R") if tipe.lower() == "progressive" else ""
            with colL:
                sph_l = st.selectbox("SPH L", [f"{x:.2f}" for x in [i * 0.25 for i in range(-24, 24)]])
                cyl_l = st.selectbox("CYL L", [f"{x:.2f}" for x in [i * 0.25 for i in range(-8,1)]])
                axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
                add_l = st.text_input("Add L") if tipe.lower() == "progressive" else ""
        else:
            st.markdown("### 🔍 Ukuran R / L (Luar Stock)")
            colR, colL = st.columns(2)
            with colR:
                sph_r = st.selectbox("SPH R", [f"{x:.2f}" for x in [i * 0.25 for i in range(-40, 41)]])
                cyl_r = st.selectbox("CYL R", [f"{x:.2f}" for x in [i * 0.25 for i in range(-20, 1)]])
                axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else ""
                add_r = st.text_input("Add R") if tipe.lower() == "progressive" else ""
            with colL:
                sph_l = st.selectbox("SPH L", [f"{x:.2f}" for x in [i * 0.25 for i in range(-40, 41)]])
                cyl_l = st.selectbox("CYL L", [f"{x:.2f}" for x in [i * 0.25 for i in range(-20, 1)]])
                axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else ""
                add_l = st.text_input("Add L") if tipe.lower() == "progressive" else ""

        # Konversi add yang dipakai (kalau progressive ambil add_r, selain itu kosong)
        add_dipakai = add_r if tipe.lower() == "progressive" else ""

        # Coba cari harga otomatis
        harga_otomatis = cari_harga_lensa_luar(
            df_lensa_luar,
            nama_lensa,
            sph_r,
            cyl_r,
            add_dipakai
        )

        if harga_otomatis:
            st.info(f"💰 Harga otomatis ditemukan: Rp {harga_otomatis:,}")
            harga_lensa = harga_otomatis



        ukuran_r = f"SPH: {sph_r}, CYL: {cyl_r}, Axis: {axis_r}, Add: {add_r}"
        ukuran_l = f"SPH: {sph_l}, CYL: {cyl_l}, Axis: {axis_l}, Add: {add_l}"

        submitted = st.form_submit_button("📝 Tambah ke Daftar Item")
        if submitted:
            st.session_state.daftar_item_luar.append({
                "tanggal_ambil": tanggal_ambil,
                "nama": nama,
                "status_lensa": status_lensa,
                "jenis": jenis,
                "tipe": tipe,
                "merk": merk,
                "nama_lensa": nama_lensa,
                "ukuran_r": ukuran_r,
                "ukuran_l": ukuran_l,
                "harga_lensa": harga_lensa,
                "ongkir": ongkir,
                "potong": potong,
                "keterangan": keterangan,
                "status_kirim": status_kirim,
                "tanggal_kirim": tanggal_kirim
                })
            st.success("Item berhasil ditambahkan!")

    # Tampilkan daftar item
    if st.session_state.daftar_item_luar:
        st.subheader("📋 Daftar Item yang Akan Disubmit")
        df = pd.DataFrame(st.session_state.daftar_item_luar)
        df["subtotal"] = df["harga_final"] + df["ongkir"] + df["potong"]
        st.dataframe(df, use_container_width=True)
        total = df["subtotal"].sum()
        st.markdown(f"### 💰 Grand Total: Rp {total:,.0f}")

        if st.button("📤 Submit Pesanan"):
            for row in df.to_dict(orient="records"):
                append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['pesanan_luar_kota'], [str(v) for v in row.values()])
            st.success("✅ Semua item berhasil disimpan!")
            del st.session_state.daftar_item_luar
