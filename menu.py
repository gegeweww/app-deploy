import streamlit as st

# Impor halaman modul
import dframe
import dlensa
import logframe
import iframe
import ilensa
import kasir
import pemb_angsuran
import logtransaksi
import luarkota
import pemb_luarkota
import logluarkota

def show_menu():
    st.sidebar.title("📦 Navigasi")
    st.sidebar.title(f"👋 Hai, {st.session_state['user']}")
    
    # Tombol untuk ganti user
    if st.sidebar.button("🔄 Ganti User"):
        st.session_state["user"] = None
        st.session_state["page"] = "pilih_user"
        st.rerun()

    menu = st.sidebar.radio("Pilih Halaman:", [
        "Kasir",        
        "History Transaksi",
        "Pembayaran Angsuran",
        "Pesanan Luar Kota",
        "Pembayaran Luar Kota",
        "History Luar Kota",
        "Data Frame",
        "Data Lensa",
        "Log Frame",
        "Input Stock Frame",
        "Input Stock Lensa"
    ])

    if menu == "Data Frame":
        dframe.run()
    elif menu == "Data Lensa":
        dlensa.run()
    elif menu == "Log Frame":
        logframe.run()
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