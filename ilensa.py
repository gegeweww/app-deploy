import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from constants import SHEET_KEY, SHEET_NAMES
from utils import (
    authorize_gspread, get_dataframe,
    append_row, buat_loglensa_status, catat_loglensa,
)

def run():
    user = st.session_state["user"]
    client = authorize_gspread()

    # Akses sheet utama
    sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["dlensa"])
    df_lensa = get_dataframe(SHEET_KEY, SHEET_NAMES["dlensa"])
    
    # Data Lensa
    Tipe_lensa_list = sorted(df_lensa['Tipe'].dropna().unique())
    SPH_list = sorted(df_lensa['SPH'].dropna().unique())
    CYL_list = sorted(df_lensa['CYL'].dropna().unique())
    Add_list = sorted(df_lensa['Add'].dropna().unique())    

    selected_Jenis, selected_Tipe, selected_merk, selected_SPH, selected_CYL, selected_Add, jumlah_input = None, None, None, None, None, None, None

    # UI Streamlit
    st.title('➕ Input Stock Lensa')
    st.write('Tambahkan stock dari Lensa yang tersedia')
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y,%H:%M:%S")
    user = st.session_state.get("user", "Unknown")
    
    # Mode Input
    selected_Tipe = st.selectbox('Pilih Tipe Lensa:', Tipe_lensa_list)
    df_filtered = df_lensa[df_lensa['Tipe'] == selected_Tipe]
    Jenis_lensa_list = sorted(df_filtered['Jenis'].dropna().unique())
    Merk_lensa_list = sorted(df_filtered['Merk'].dropna().unique())

    selected_Jenis = st.selectbox('Pilih Jenis Lensa:', Jenis_lensa_list)
    selected_merk = st.selectbox('Pilih Merk Lensa:', Merk_lensa_list)
    selected_SPH = st.selectbox('Pilih SPH:', SPH_list)
    selected_CYL = st.selectbox('Pilih CYL:', CYL_list)
    jumlah_input = st.number_input('Jumlah', min_value=0, step=1)
    if selected_Tipe != 'Single Vision':
        selected_Add = None
    else:
        selected_Add = st.selectbox('Pilih Add:', Add_list)
        
    if st.button('Tambah'):
        filter_stock = df_lensa[
            (df_lensa['Jenis'] == selected_Jenis) &
            (df_lensa['Tipe'] == selected_Tipe) &
            (df_lensa['merk'] == selected_merk) &
            (df_lensa['SPH'] == selected_SPH) &
            (df_lensa['CYL'] == selected_CYL) &
            (df_lensa['Add'] == selected_Add)
        ]
        
        if not filter_stock.empty:
            stock_lama = int(filter_stock['stock'].values[0])
            stock_baru = stock_lama + jumlah_input
            
            cell = sheet.find(selected_merk)
            if cell:
                sheet.update_cell(cell.row, 10, stock_baru)
                with st.expander("📦 Stock berhasil diperbarui"):
                    st.markdown(f"""
                        **Jenis:** {selected_Jenis}  
                        **Tipe:** {selected_Tipe}  
                        **Merk:** {selected_merk}  
                        **SPH:** {selected_SPH}  
                        **CYL:** {selected_CYL}  
                        **Add:** {selected_Add}  
                        **Jumlah Ditambahkan:** {jumlah_input}  
                        **Total Sekarang:** {stock_baru}
                    """)
                              
                buat_loglensa_status(
                    sheet_key=SHEET_KEY,
                    sheet_name=SHEET_NAMES["loglensa"],
                    merk=selected_merk,
                    Tipe=selected_Tipe,
                    Jenis=selected_Jenis,
                    SPH=selected_SPH,
                    CYL=selected_CYL,
                    Add=selected_Add
                )
                catat_loglensa(
                    sheet_key=SHEET_KEY,
                    sheet_name=SHEET_NAMES["loglensa"],
                    source="ilensa",
                    merk=selected_merk,
                    Tipe=selected_Tipe,
                    Jenis=selected_Jenis,
                    SPH=selected_SPH,
                    CYL=selected_CYL,
                    Add=selected_Add,
                    jumlah_input=jumlah_input,
                    stock_lama=stock_lama,
                    stock_baru=stock_baru,
                    user=user
                )
        else:
            st.error("Data tidak ditemukan. Silakan periksa input Anda.")