import streamlit as st

def show_menu():
    # Impor halaman modul
    import dframe
    import dlensa
    import logframe
    import loglensa
    import iframe
    import ilensa
    import kasir
    import pemb_angsuran
    import logtransaksi
    import luarkota
    import pemb_luarkota
    import logluarkota
    import dashboard
    import pelanggan
    import manajemen_stock

    st.sidebar.title("Optik Maroon")
    st.sidebar.title(f"👋 Hai, {st.session_state['user']}")
    
    # Tombol untuk ganti user
    if st.sidebar.button("🔄 Ganti User"):
        st.session_state["user"] = None
        st.session_state["page"] = "pilih_user"
        st.rerun()

    menu = st.sidebar.radio("Pilih Halaman:", [
        "Dashboard",
        "Data Pelanggan",
        "Kasir",        
        "History Transaksi",
        "Pembayaran Angsuran",
        "Pesanan Luar Kota",
        "Pembayaran Luar Kota",
        "History Luar Kota",
        "Data Frame",
        "Data Lensa",
        "Log Frame",
        "Log Lensa",
        "Input Stock Frame",
        "Input Stock Lensa",
        "Manajemen Stock"
    ])
    if menu == "Dashboard":
        dashboard.run()
    elif menu == "Data Pelanggan":
        pelanggan.run()
    elif menu == "Data Frame":
        dframe.run()
    elif menu == "Data Lensa":
        dlensa.run()
    elif menu == "Log Frame":
        logframe.run()
    elif menu == "Log Lensa":
        loglensa.run()
    elif menu == "Input Stock Frame":
        iframe.run()
    elif menu == "Kasir":
        kasir.run()
    elif menu == "Pembayaran Angsuran":
        pemb_angsuran.run()
    elif menu == "History Transaksi":
        logtransaksi.run()
    elif menu == "Pesanan Luar Kota":
        luarkota.run()
    elif menu == "Pembayaran Luar Kota":
        pemb_luarkota.run()
    elif menu == "History Luar Kota":
        logluarkota.run()
    elif menu == "Input Stock Lensa":
        ilensa.run()
    elif menu == "Manajemen Stock":
        manajemen_stock.run()