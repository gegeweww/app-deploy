import streamlit as st
from menu import show_menu
from utils import set_font

st.set_page_config(page_title="Optik Maroon Pontianak", layout="centered", initial_sidebar_state="expanded")
set_font()
st.markdown("""
<style>
[data-testid="stIconMaterial"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

from utils import get_table_cached

@st.cache_data(ttl=300)
def load_users():
    df = get_table_cached("user_name")
    return sorted(df["user_name"].dropna().tolist())

users = load_users()

# Setup session
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "login"
    
PASSWORD = st.secrets["auth"]["password"]

def login():
    st.title("Login")

    password = st.text_input("Password", type="password")

    if st.button("Masuk"):
        if password == st.secrets["auth"]["password"]:
            st.success("Login berhasil!")
            st.session_state["logged_in"] = True
            st.session_state["page"] = "pilih_user"
            st.rerun()
        else:
            st.error("Password salah!")

def pilih_user():
    st.title("Optik Maroon Pontianak")
    st.title("👤 Pilih User")
    selected = st.selectbox(
        "Pilih User",
        options=users,
        index=None,
        format_func=lambda x: x if x else "— pilih user —"
    )
    if st.button("Lanjut"):
        st.session_state["user"] = selected
        st.session_state["page"] = "menu"
        st.rerun()

# Navigasi halaman
if st.session_state["logged_in"] is False:
    login()
if st.session_state["page"] == "pilih_user":
    pilih_user()
elif st.session_state["page"] == "menu":
    show_menu()
