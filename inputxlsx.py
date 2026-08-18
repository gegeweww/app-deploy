import streamlit as st

from tools.frame.frame_import import (
    load_excel,
    create_template_excel,
    validate_header,
    compare_frames,
    update_frames
)


def run():

    st.title("Input Data Frame")

    st.markdown("""
        Langkah-Langkah Upload Data:
        - Download template
        - Isi data
        - Upload file
        - Sistem akan memvalidasi format
    """)

    # ==========================================
    # TEMPLATE EXCEL
    # ==========================================

    st.subheader("Template Excel")

    template = create_template_excel()

    st.download_button(
        label="📥 Download Template Frame.xlsx",
        data=template,
        file_name="Template_Frame.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    # ==========================================
    # UPLOAD EXCEL
    # ==========================================

    st.subheader("Upload Excel")

    file = st.file_uploader(
        "Upload Data Excel Frame",
        type="xlsx"
    )

    if not file:
        return

    # ==========================================
    # BACA EXCEL
    # ==========================================

    df = load_excel(file)

    # ==========================================
    # VALIDASI HEADER
    # ==========================================

    if not validate_header(df):

        st.error(
            "Format Excel tidak sesuai"
        )

        return

    # ==========================================
    # COMPARE DATABASE
    # ==========================================

    df_update, df_new = compare_frames(df)

    # ==========================================
    # PREVIEW UPDATE STOCK
    # ==========================================

    st.subheader("📦 Update Stock")

    st.dataframe(
        df_update,
        use_container_width=True
    )

    # ==========================================
    # PREVIEW DATA BARU
    # ==========================================

    st.subheader("🆕 Data Baru")

    st.dataframe(
        df_new,
        use_container_width=True
    )

    # ==========================================
    # TOMBOL UPDATE
    # ==========================================

    if st.button(
        "Update Frame",
        type="primary"
    ):

        user = st.session_state.get(
            "user_name",
            "Unknown"
        )

        # ======================================
        # EKSEKUSI UPDATE / INSERT
        # ======================================

        hasil = update_frames(
            df_update,
            df_new,
            user=user
        )

        # ======================================
        # SUCCESS MESSAGE
        # ======================================

        st.success(
            "Data frame berhasil dimasukkan ke database."
        )

        # ======================================
        # FRAME YANG DI-UPDATE
        # ======================================

        if hasil["updated"]:

            with st.expander(
                f"📦 Frame berhasil diperbarui "
                f"({len(hasil['updated'])})",
                expanded=True
            ):

                for merk, kode in hasil["updated"]:

                    st.write(
                        f"• **{merk}** — {kode}"
                    )

        # ======================================
        # FRAME BARU
        # ======================================

        if hasil["inserted"]:

            with st.expander(
                f"🆕 Frame baru berhasil ditambahkan "
                f"({len(hasil['inserted'])})",
                expanded=True
            ):

                for merk, kode in hasil["inserted"]:

                    st.write(
                        f"• **{merk}** — {kode}"
                    )