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
    tipe_lensa_list = sorted(df_lensa['tipe'].dropna().unique())
    jenis_lensa_list = sorted(df_lensa[df_lensa['tipe'] == tipe_lensa_list]['jenis'].dropna().unique())
    merk_lensa_list = sorted(df_lensa[df_lensa['tipe'] == tipe_lensa_list]['merk'].dropna().unique())
    sph_list = sorted(df_lensa['sph'].dropna().unique())
    cyl_list = sorted(df_lensa['cyl'].dropna().unique())
    add_list = sorted(df_lensa['add'].dropna().unique())    

    selected_jenis, selected_tipe, selected_merk, selected_sph, selected_cyl, selected_add, jumlah_input = None, None, None, None, None, None, None

    # UI Streamlit
    st.title('➕ Input Stock Lensa')
    st.write('Tambahkan stock dari Lensa yang tersedia')
    today = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y,%H:%M:%S")
    user = st.session_state.get("user", "Unknown")
    
    # Mode Input
    selected_jenis = st.selectbox('Pilih Jenis Lensa:', jenis_lensa_list)
    selected_tipe = st.selectbox('Pilih Tipe Lensa:', tipe_lensa_list)
    selected_merk = st.selectbox('Pilih Merk Lensa:', merk_lensa_list)
    selected_sph = st.selectbox('Pilih Sph:', sph_list)
    selected_cyl = st.selectbox('Pilih Cyl:', cyl_list)
    jumlah_input = st.number_input('Jumlah', min_value=0, step=1)
    if selected_tipe != 'Single Vision':
        selected_add = None
    else:
        selected_add = st.selectbox('Pilih Add:', add_list)
        
    if st.button('Tambah'):
        filter_stock = df_lensa[
            (df_lensa['jenis'] == selected_jenis) &
            (df_lensa['tipe'] == selected_tipe) &
            (df_lensa['merk'] == selected_merk) &
            (df_lensa['sph'] == selected_sph) &
            (df_lensa['cyl'] == selected_cyl) &
            (df_lensa['add'] == selected_add)
        ]
        
        if not filter_stock.empty:
            stock_lama = int(filter_stock['stock'].values[0])
            stock_baru = stock_lama + jumlah_input
            
            cell = sheet.find(selected_merk)
            if cell:
                sheet.update_cell(cell.row, 10, stock_baru)
                with st.expander("📦 Stock berhasil diperbarui"):
                    st.markdown(f"""
                        **Jenis:** {selected_jenis}  
                        **Tipe:** {selected_tipe}  
                        **Merk:** {selected_merk}  
                        **Sph:** {selected_sph}  
                        **Cyl:** {selected_cyl}  
                        **Add:** {selected_add}  
                        **Jumlah Ditambahkan:** {jumlah_input}  
                        **Total Sekarang:** {stock_baru}
                    """)
                              
                buat_loglensa_status(
                    sheet_key=SHEET_KEY,
                    sheet_name=SHEET_NAMES["loglensa"],
                    merk=selected_merk,
                    tipe=selected_tipe,
                    jenis=selected_jenis,
                    sph=selected_sph,
                    cyl=selected_cyl,
                    add=selected_add
                )
                catat_loglensa(
                    sheet_key=SHEET_KEY,
                    sheet_name=SHEET_NAMES["loglensa"],
                    source="ilensa",
                    merk=selected_merk,
                    tipe=selected_tipe,
                    jenis=selected_jenis,
                    sph=selected_sph,
                    cyl=selected_cyl,
                    add=selected_add,
                    jumlah_input=jumlah_input,
                    stock_lama=stock_lama,
                    stock_baru=stock_baru,
                    user=user
                )
            with st.expander('Stock Lensa berhasil diperbarui'):
                st.markdown(f"""
                    **Jenis:** {selected_jenis}  
                    **Tipe:** {selected_tipe}  
                    **Merk:** {selected_merk}  
                    **Sph:** {selected_sph}  
                    **Cyl:** {selected_cyl}  
                    **Add:** {selected_add}  
                    **Jumlah Ditambahkan:** {jumlah_input}  
                    **Total Sekarang:** {stock_baru}
                """)
        else:
            st.error("Data tidak ditemukan. Silakan periksa input Anda.")