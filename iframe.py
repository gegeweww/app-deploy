import streamlit as st
from datetime import datetime
from constants import SHEET_KEY, JSON_PATH, SHEET_NAMES
from utils import (
    get_dataframe, get_gsheet_client, 
    append_row, buat_logframe_status, catat_logframe
)


def run():
    user = st.session_state["user"]
    client = get_gsheet_client(JSON_PATH)

    # Akses sheet utama
    sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["dframe"])

    df = get_dataframe(SHEET_KEY, JSON_PATH, SHEET_NAMES["dframe"])
    df['Kode'] = df['Kode'].astype(str)

    # Data Frame
    selected_merk, selected_kode, jumlah_input, distributor = None, None, None, None
    merk_list = sorted(df['Merk'].dropna().unique())

    # UI Streamlit
    st.title('➕ Input / Edit Stock Frame')
    st.write('Tambahkan atau ubah stock dari frame yang tersedia')
    today = datetime.today().strftime("%Y-%m-%d,%H:%M:%S")
    user = st.session_state.get("user", "Unknown")

    # Mode
    mode = st.selectbox('Pilih Mode:', ['Tambah Stock', 'Tambah Merk', 'Tambah Kode'])
    if mode == 'Tambah Stock':
        selected_merk = st.selectbox('Pilih Merk Frame:', merk_list)
        filtered_df = df[df['Merk'] == selected_merk]
        kode_list = sorted(filtered_df['Kode'].unique())
        selected_kode = st.selectbox('Pilih Kode Frame:', kode_list)
        jumlah_input = st.number_input('Jumlah', min_value=0, step=1)

        if st.button('Tambah'):
            filter_stock = df[(df['Merk'] == selected_merk) & (df['Kode'] == selected_kode)]
            if not filter_stock.empty:
                stock_lama = int(filter_stock['Stock'].values[0])
                stock_baru = stock_lama + jumlah_input

                cell = sheet.find(selected_kode)
                if cell:
                    sheet.update_cell(cell.row, 6, stock_baru)
                    with st.expander("📦 Stock berhasil diperbarui"):
                        st.markdown(f"""
                            **Merk:** {selected_merk}  
                            **Kode:** {selected_kode}  
                            **Jumlah Ditambahkan:** {jumlah_input}  
                            **Total Sekarang:** {stock_baru}
                        """)

                    catat_logframe(
                        sheet_key=SHEET_KEY,
                        json_path=JSON_PATH,
                        merk=selected_merk,
                        kode=selected_kode,
                        source="iframe",
                        mode=mode,
                        jumlah_input=jumlah_input,
                        stock_lama=stock_lama,
                        stock_baru=stock_baru,
                        user=user
                    )
            else:
                st.error("Data frame tidak menemukan kode tersebut.")

    elif mode == 'Tambah Merk':
        selected_merk = st.text_input('Masukan Merk Baru')
        selected_kode = st.text_input('Masukan Kode Baru')
        distributor = st.text_input('Masukan Nama Distributor')
        harga_modal = st.number_input('Masukan Harga Modal', min_value=0, step=1000)
        harga_jual = st.number_input('Masukan Harga Jual', min_value=0, step=1000)
        stock_baru = st.number_input('Jumlah', min_value=0, step=1)

        if st.button('Tambah'):
            if selected_merk in df['Merk'].unique():
                st.warning("Merk ini sudah terdaftar. Silakan ubah ke mode Tambah Stock atau Tambah Kode.")
                st.stop()
            frame_data = [selected_merk, selected_kode, distributor, harga_modal, harga_jual, stock_baru]
            append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['dframe'], frame_data)
            sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["dframe"])
            sheet.sort((1, 'asc'), range='A2:F')  # Sort by column 1 (Merk) A-Z

            with st.expander("📦 Stock baru berhasil ditambahkan"):
                st.markdown(f"""
                    **Merk:** {selected_merk}  
                    **Kode:** {selected_kode}  
                    **Distributor:** {distributor}  
                    **Harga Modal:** {harga_modal}  
                    **Harga Jual:** {harga_jual}  
                    **Jumlah:** {stock_baru}
                """)

            catat_logframe(
                sheet_key=SHEET_KEY,
                json_path=JSON_PATH,
                merk=selected_merk,
                kode=selected_kode,
                source="iframe",
                mode=mode,
                stock_baru=stock_baru,
                user=user
            )

    elif mode == 'Tambah Kode':
        selected_merk = st.selectbox('Pilih Merk Frame:', merk_list)
        selected_kode = st.text_input('Masukan Kode Baru')
        filtered_df = df[df['Merk'] == selected_merk]
        distributor = filtered_df['Distributor'].values[0] if not filtered_df.empty else ""
        harga_modal = st.number_input('Masukan Harga Modal', min_value=0, step=1000)
        harga_jual = st.number_input('Masukan Harga Jual', min_value=0, step=1000)
        stock_baru = st.number_input('Jumlah', min_value=0, step=1)

        if st.button('Tambah'):
            if ((df['Merk'] == selected_merk) & (df['Kode'] == selected_kode)).any():
                st.warning("Merk dan kode ini sudah terdaftar. Silakan ubah ke mode Tambah Stock.")
                st.stop()

            frame_data = [selected_merk, selected_kode, distributor, harga_modal, harga_jual, stock_baru]
            append_row(SHEET_KEY, JSON_PATH, SHEET_NAMES['dframe'], frame_data)
            sheet = client.open_by_key(SHEET_KEY).worksheet(SHEET_NAMES["dframe"])
            sheet.sort((1, 'asc'))  # Sort by column 1 (Merk) A-Z
            
            with st.expander("📦 Kode baru berhasil ditambahkan"):
                st.markdown(f"""
                    **Merk:** {selected_merk}  
                    **Kode:** {selected_kode}  
                    **Distributor:** {distributor}  
                    **Harga Modal:** {harga_modal}  
                    **Harga Jual:** {harga_jual}  
                    **Jumlah:** {stock_baru}
                """)

            catat_logframe(
                sheet_key=SHEET_KEY,
                json_path=JSON_PATH,
                merk=selected_merk,
                kode=selected_kode,
                source="iframe",
                mode=mode,
                stock_baru=stock_baru,
                user=user
            )
