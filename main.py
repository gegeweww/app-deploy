import streamlit as st
from menu import show_menu
from constants import USERS
from utils import set_font

st.set_page_config(page_title="Optik Maroon Pontianak", layout="centered")
set_font()
st.markdown("""
    <style>
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

def pilih_user():
    st.title("Optik Maroon Pontianak")
    st.title("👤 Pilih User")
    selected = st.selectbox("Pilih User", options=USERS, index=None, format_func=lambda x: x if x else "— pilih user —")

    if st.button("Lanjut"):
        st.session_state["user"] = selected
        st.session_state["page"] = "menu"
        st.rerun()

# Setup session
if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "pilih_user"

# Navigasi halaman
if st.session_state["page"] == "pilih_user":
    pilih_user()
elif st.session_state["page"] == "menu":
    show_menu()
