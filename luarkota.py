import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils import (
    get_table_cached, insert_row_supabase, get_supabase,
    generate_id_skw_supabase, generate_id_pemb_skw_supabase,
    cari_harga_lensa_luar, cari_harga_lensa_stock,
    catat_loglensa_supabase
)

@st.dialog("✅ Pembayaran Berhasil")
def dialog_ringkasan_luarkota(data, reset_func):
    st.markdown(f"""
    **Tanggal Transaksi:** {data['tanggal']}  
    **ID Transaksi:** `{data['id_transaksi']}`  
    **Nama:** {data['nama']}  
    **Status:** {data['status']}  
    **Sisa/Kembalian:** Rp {data['sisa']:,.0f}
    """)
    if st.button("OK"):
        reset_func()
        st.rerun()

def now_jkt():
    return datetime.now(ZoneInfo("Asia/Jakarta")).replace(microsecond=0)

def run():
    @st.cache_data(ttl=60)
    def load_data():
        df_lensa_stock = get_table_cached("lensa")
        df_lensa_luar = get_table_cached("lensa_luar_stock")
        return df_lensa_stock, df_lensa_luar

    df_lensa_stock, df_lensa_luar = load_data()

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

    st.title("📦 Pesanan Luar Kota")
    today = now_jkt().strftime("%d-%m-%Y, %H:%M:%S")

    colL, colR = st.columns(2)
    with colL:
        tanggal_ambil = st.date_input("📅 Tanggal Ambil", value=date.today(), format="DD/MM/YYYY")
    with colR:
        nama = st.selectbox("Nama Konsumen", ["Rahmat", "Nelly"])

    if "daftar_item_luar" not in st.session_state:
        st.session_state.daftar_item_luar = []

    st.subheader("➕ Tambah Item")

    status_lensa = st.selectbox("Status Lensa", ["Stock", "Inti", "Pesan", "Overlens"])

    if status_lensa == "Stock":
        df_lensa = df_lensa_stock.copy()
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

    nama_lensa = ""

    if status_lensa == "Stock":
        st.markdown("**Ukuran Lensa**")
        colR, colL = st.columns(2)

        sph_list = sorted(df_lensa['sph'].dropna().unique())
        cyl_list = sorted(df_lensa['cyl'].dropna().unique())

        with colR:
            sph_r = st.selectbox("SPH R", sph_list, index=sph_list.index("0.00"))
            cyl_r = st.selectbox("CYL R", cyl_list, index=cyl_list.index("0.00"))
            axis_r = st.selectbox("Axis R", list(range(0, 181))) if cyl_r != "0.00" else None
            add_r = st.selectbox("Add R", sorted(df_lensa['add_power'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""
        with colL:
            sph_l = st.selectbox("SPH L", sph_list, index=sph_list.index("0.00"))
            cyl_l = st.selectbox("CYL L", cyl_list, index=cyl_list.index("0.00"))
            axis_l = st.selectbox("Axis L", list(range(0, 181))) if cyl_l != "0.00" else None
            add_l = st.selectbox("Add L", sorted(df_lensa['add_power'].dropna().unique())) if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""

    else:
        nama_lensa = st.selectbox("Nama Lensa", sorted(df_lensa[
            (df_lensa['jenis'] == jenis_lensa) &
            (df_lensa['tipe'] == tipe_lensa) &
            (df_lensa['merk'] == merk_lensa)
        ]['nama_lensa'].dropna().unique()))

        st.markdown("**Ukuran Lensa**")
        colR, colL = st.columns(2)

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

    add_dipakai = add_r if tipe_lensa in ["Progressive", "Kryptok", "Flattop"] else ""

    if status_lensa == "Stock":
        harga_lensa = cari_harga_lensa_stock(df_lensa, tipe_lensa, jenis_lensa, merk_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=True)
        if harga_lensa is None:
            st.warning("⚠️ Harga lensa stock tidak ditemukan!")
            st.stop()
    else:
        harga_lensa = cari_harga_lensa_luar(df_lensa, tipe_lensa, jenis_lensa, nama_lensa, sph_r, cyl_r, add_dipakai, pakai_reseller=True)
        if harga_lensa is None:
            st.warning("⚠️ Ukuran tidak sesuai rentang harga manapun!")
            st.stop()

    st.markdown(f"#### Harga lensa: Rp {harga_lensa:,.0f}")
    diskon = st.number_input("Diskon Lensa (Rp)", min_value=0, step=1000)
    tambahan = st.number_input("Tambahan (Rp)", min_value=0, step=1000)
    potong = st.selectbox("Ongkos Potong", [17000, 27000, 32000])
    keterangan = st.text_area("Keterangan Tambahan")

    # Ongkir hanya untuk status lensa "Pesan"
    ONGKIR_PER_LENSA = 25000
    ongkir_item = ONGKIR_PER_LENSA if status_lensa == "Pesan" else 0
    subtotal = harga_lensa + potong + tambahan + ongkir_item


    if st.button("📝 Tambah ke Daftar"):
        # ===================== CEK STOK =====================
        if status_lensa == "Stock":
            for side, sph, cyl, add in [
                ("Kanan", sph_r, cyl_r, add_r),
                ("Kiri", sph_l, cyl_l, add_l),
            ]:
                kondisi = (
                    (df_lensa_stock["jenis"] == jenis_lensa) &
                    (df_lensa_stock["tipe"] == tipe_lensa) &
                    (df_lensa_stock["merk"] == merk_lensa) &
                    (df_lensa_stock["sph"] == sph) &
                    (df_lensa_stock["cyl"] == cyl)
                )
                if tipe_lensa.lower() != "single vision":
                    kondisi = kondisi & (df_lensa_stock["add_power"] == add)

                df_match = df_lensa_stock[kondisi]

                if df_match.empty:
                    st.warning(f"Data lensa {side} tidak ditemukan: {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph} CYL {cyl}")
                    st.stop()

                if len(df_match) > 1:
                    st.error("Terjadi duplikasi data lensa di database!")
                    st.stop()

                try:
                    stock_lama = int(str(df_match.iloc[0]["stock"]).replace(",", "").strip())
                except Exception:
                    stock_lama = 0

                if stock_lama <= 0:
                    st.warning(f"Stock lensa {side} habis: {merk_lensa} {tipe_lensa} {jenis_lensa} SPH {sph} CYL {cyl}")
                    st.stop()

        st.session_state.daftar_item_luar.append({
            "tanggal_ambil": tanggal_ambil,
            "nama": nama,
            "status_lensa": status_lensa,
            "jenis_lensa": jenis_lensa,
            "tipe_lensa": tipe_lensa,
            "merk_lensa": merk_lensa,
            "nama_lensa": nama_lensa,
            "sph_r": sph_r, "cyl_r": cyl_r, "axis_r": axis_r, "add_r": add_r,
            "sph_l": sph_l, "cyl_l": cyl_l, "axis_l": axis_l, "add_l": add_l,
            "harga_lensa": harga_lensa,
            "potong": potong,
            "ongkir": ongkir_item,
            "tambahan": tambahan,
            "subtotal": subtotal,
            "diskon": diskon,
            "keterangan": keterangan,
        })
        st.success("Item berhasil ditambahkan!")

    if st.session_state.daftar_item_luar:
        st.subheader("📋 Daftar Item")

        for i, item in enumerate(st.session_state.daftar_item_luar):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**Item {i+1}:** {item['merk_lensa']} - {item['nama_lensa']} ({item['jenis_lensa']}, {item['tipe_lensa']})")
            with col2:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state.daftar_item_luar.pop(i)
                    st.rerun()

        df_raw = pd.DataFrame(st.session_state.daftar_item_luar)

        df_display = df_raw.rename(columns={
            "tanggal_ambil": "Tanggal Ambil",
            "nama": "Nama",
            "status_lensa": "Status Lensa",
            "jenis_lensa": "Jenis Lensa",
            "tipe_lensa": "Tipe Lensa",
            "merk_lensa": "Merk Lensa",
            "nama_lensa": "Nama Lensa",
            "sph_r": "SPH R", "cyl_r": "CYL R", "axis_r": "Axis R", "add_r": "Add R",
            "sph_l": "SPH L", "cyl_l": "CYL L", "axis_l": "Axis L", "add_l": "Add L",
            "harga_lensa": "Harga Lensa",
            "potong": "Ongkos Potong",
            "ongkir": "Ongkir",
            "tambahan": "Tambahan",
            "subtotal": "Subtotal",
            "diskon": "Diskon",
            "keterangan": "Keterangan"
        })

        kolom_rupiah = ["Harga Lensa", "Ongkos Potong", "Ongkir", "Tambahan", "Diskon", "Subtotal"]
        for col in kolom_rupiah:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: f"Rp {int(x):,}".replace(",", ".") if pd.notnull(x) else "Rp 0"
                )

        st.dataframe(df_display, width='stretch')

        # Hitung total (subtotal item - diskon + ongkir 1x)
        total_item = sum(item["subtotal"] - item["diskon"] for item in st.session_state.daftar_item_luar)
        total = total_item

        st.markdown(f"##### Subtotal Item: Rp {total_item:,.0f}")
        st.markdown(f"#### 💰 Total Harga: Rp {total:,.0f}")

        via = st.selectbox("Via Pembayaran", ["Cash", "TF BCA", "TF Mandiri"])
        nominal = st.number_input("Masukkan Nominal", min_value=0)
        sisa = total - nominal
        if sisa <= 0:
            status = "Lunas"
            sisa = 0
        else:
            status = "Belum Lunas"

        metode = "Full" if status == "Lunas" else "Angsuran"

        if st.button("📤 Submit Pembayaran"):
            st.session_state['simpan_pembayaran'] = True

    # ===================== SIMPAN =====================
    if st.session_state.get('simpan_pembayaran', False):
        id_transaksi = generate_id_skw_supabase(nama, tanggal_ambil)
        id_pembayaran = generate_id_pemb_skw_supabase(nama, tanggal_ambil)
        user = st.session_state.get("user", "Unknown")
        supabase = get_supabase()

        total_item = sum(item["subtotal"] - item["diskon"] for item in st.session_state.daftar_item_luar)
        total = total_item

        # ===================== INSERT HEADER =====================
        insert_row_supabase("pesanan_luar_kota", {
            "timestamp_log": now_jkt(),
            "tanggal_ambil": tanggal_ambil,
            "id_transaksi": id_transaksi,
            "nama": nama,
            "total_harga": int(total),
            "user_name": user
        })

        # ===================== INSERT DETAIL + UPDATE STOK =====================
        for item in st.session_state.daftar_item_luar:
            insert_row_supabase("pesanan_luar_kota_detail", {
                "timestamp_log": now_jkt(),
                "tanggal_ambil": tanggal_ambil,
                "id_transaksi": id_transaksi,
                "nama": item["nama"],
                "status_lensa": item["status_lensa"],
                "jenis_lensa": item["jenis_lensa"],
                "tipe_lensa": item["tipe_lensa"],
                "merk_lensa": item["merk_lensa"],
                "nama_lensa": item["nama_lensa"],
                "sph_r": item["sph_r"], "cyl_r": item["cyl_r"],
                "axis_r": item["axis_r"], "add_r": item["add_r"],
                "sph_l": item["sph_l"], "cyl_l": item["cyl_l"],
                "axis_l": item["axis_l"], "add_l": item["add_l"],
                "harga_lensa": item["harga_lensa"],
                "ongkos_potong": item["potong"],
                "ongkir": item["ongkir"],
                "tambahan": item["tambahan"],
                "diskon": item["diskon"],
                "keterangan": item["keterangan"],
                "total_harga": item["subtotal"] - item["diskon"],
                "user_name": user
            })

            # ===================== UPDATE STOK LENSA =====================
            if item['status_lensa'] == "Stock":
                for side in ["r", "l"]:
                    sph = item[f"sph_{side}"]
                    cyl = item[f"cyl_{side}"]
                    add = item[f"add_{side}"]

                    query = (
                        supabase.table("lensa")
                        .select("id, stock")
                        .eq("tipe", item["tipe_lensa"])
                        .eq("jenis", item["jenis_lensa"])
                        .eq("merk", item["merk_lensa"])
                        .eq("sph", sph)
                        .eq("cyl", cyl)
                    )
                    if add:
                        query = query.eq("add_power", add)
                    else:
                        query = query.is_("add_power", None)

                    result = query.execute()

                    if not result.data:
                        st.warning(f"Data lensa tidak ditemukan: {item['merk_lensa']} {item['tipe_lensa']} {item['jenis_lensa']} SPH {sph} CYL {cyl}")
                        st.stop()

                    record = result.data[0]
                    stock_lama = record["stock"] or 0

                    if stock_lama <= 0:
                        st.warning(f"Stock habis: {item['merk_lensa']} {item['tipe_lensa']} {item['jenis_lensa']} SPH {sph} CYL {cyl}")
                        st.stop()

                    supabase.table("lensa") \
                        .update({"stock": stock_lama - 1}) \
                        .eq("id", record["id"]) \
                        .execute()

                    catat_loglensa_supabase(
                        jenis=item["jenis_lensa"],
                        tipe=item["tipe_lensa"],
                        merk=item["merk_lensa"],
                        sph=sph, cyl=cyl, add_power=add,
                        source="luarkota",
                        status_lensa="Stock",
                        id_transaksi=id_transaksi,
                        nama=nama,
                        user=user
                    )

        # ===================== INSERT PEMBAYARAN =====================
        insert_row_supabase("pembayaran_luar_kota", {
            "timestamp_log": now_jkt(),
            "tanggal_ambil": tanggal_ambil,
            "tanggal_bayar": tanggal_ambil,
            "id_transaksi": id_transaksi,
            "id_pembayaran": id_pembayaran,
            "nama": nama,
            "metode": metode,
            "via": via,
            "total_harga": int(total),
            "nominal_pembayaran": int(nominal),
            "sisa": int(sisa),
            "pembayaran_ke": 1,
            "status": status,
            "user_name": user
        })

        st.session_state['ringkasan_tersimpan'] = {
            "tanggal": today,
            "id_transaksi": id_transaksi,
            "nama": nama,
            "status": status,
            "sisa": sisa
        }
        st.session_state['simpan_pembayaran'] = False
        st.rerun()

    def reset_form_luarkota():
        st.session_state.pop("daftar_item_luar", None)
        st.session_state.pop("simpan_pembayaran", None)
        st.session_state.pop("ringkasan_tersimpan", None)

    if 'ringkasan_tersimpan' in st.session_state:
        dialog_ringkasan_luarkota(st.session_state['ringkasan_tersimpan'], reset_form_luarkota)
