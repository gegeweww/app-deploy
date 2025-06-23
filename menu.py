import streamlit as st

# Impor halaman modul
import dframe
import dlensa
import logframe
import iframe
import kasircb
import pemb_angsuran
import logtransaksi
import luarkota

def show_menu():
    st.sidebar.title("📦 Navigasi")
    st.sidebar.title(f"👋 Hai, {st.session_state['user']}")
    
    # Tombol untuk ganti user
    if st.sidebar.button("🔄 Ganti User"):
        st.session_state["user"] = None
        st.session_state["page"] = "pilih_user"
        st.rerun()

    menu = st.sidebar.radio("Pilih Halaman:", [
        "📊 Data Frame",
        "📊 Data Lensa",
        "📄 Log Frame",
        "➕ Input Stock Frame",
        "Kasir",
        "Pembayaran Angsuran",
        "History Transaksi",
        "Pesanan Luar Kota"
    ])

    if menu == "📊 Data Frame":
        dframe.run()
    elif menu == "📊 Data Lensa":
        dlensa.run()
    elif menu == "📄 Log Frame":
        logframe.run()
    elif menu == "➕ Input Stock Frame":
        iframe.run()
    elif menu == "Kasir":
        kasircb.run()
    elif menu == "Pembayaran Angsuran":
        pemb_angsuran.run()
    elif menu == "History Transaksi":
        logtransaksi.run()
    elif menu == "Pesanan Luar Kota":
        luarkota.run()