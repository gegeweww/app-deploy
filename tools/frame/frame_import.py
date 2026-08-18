import pandas as pd
from io import BytesIO

from utils import get_table_raw, get_supabase

from tools.frame.frame_log import (
    log_frame_baru,
    log_frame_stock,
    log_frame_distributor,
    log_frame_harga
)


def load_excel(file):
    return pd.read_excel(file)


def create_template_excel():

    df_template = pd.DataFrame(
        columns=[
            "merk",
            "kode",
            "distributor",
            "harga_modal",
            "harga_jual",
            "stock"
        ]
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df_template.to_excel(
            writer,
            index=False,
            sheet_name="Frame"
        )

    output.seek(0)

    return output


def validate_header(df):

    required = [
        "merk",
        "kode",
        "distributor",
        "harga_modal",
        "harga_jual",
        "stock"
    ]

    return list(df.columns) == required


def normalize_key(merk, kode):

    return (
        str(merk).strip().upper(),
        str(kode).strip().upper()
    )


def compare_frames(df_excel):

    df_db = get_table_raw("frames")

    df_db["key"] = df_db.apply(
        lambda x: normalize_key(
            x["merk"],
            x["kode"]
        ),
        axis=1
    )

    db_dict = df_db.set_index("key").to_dict("index")

    update_data = []
    new_data = []

    for _, row in df_excel.iterrows():

        key = normalize_key(
            row["merk"],
            row["kode"]
        )

        # ==========================================
        # DATA SUDAH ADA
        # ==========================================

        if key in db_dict:

            old = db_dict[key]

            warning = []

            # --------------------------------------
            # DISTRIBUTOR
            # --------------------------------------

            distributor_lama = old["distributor"]

            if pd.isna(row["distributor"]):

                distributor_baru = distributor_lama

            else:

                distributor_baru = row["distributor"]

                if (
                    not pd.isna(distributor_lama)
                    and distributor_lama != distributor_baru
                ):
                    warning.append(
                        f"Distributor: "
                        f"{distributor_lama} → "
                        f"{distributor_baru}"
                    )

            # --------------------------------------
            # HARGA JUAL
            # --------------------------------------

            harga_jual_lama = old["harga_jual"]
            harga_jual_baru = row["harga_jual"]

            if harga_jual_lama != harga_jual_baru:

                warning.append(
                    f"Harga jual: "
                    f"{harga_jual_lama} → "
                    f"{harga_jual_baru}"
                )

            # --------------------------------------
            # STOCK
            # --------------------------------------

            stock_lama = old["stock"]
            stock_tambah = row["stock"]

            stock_akhir = stock_lama + stock_tambah

            # --------------------------------------
            # SIMPAN DATA UPDATE
            # --------------------------------------

            update_data.append({

                "id": old["id"],

                "merk": row["merk"],
                "kode": row["kode"],

                "stock_lama": stock_lama,
                "stock_tambah": stock_tambah,
                "stock_akhir": stock_akhir,

                "distributor_lama": distributor_lama,
                "distributor_baru": distributor_baru,

                "harga_modal_lama": old["harga_modal"],
                "harga_modal_baru": row["harga_modal"],

                "harga_jual_lama": harga_jual_lama,
                "harga_jual_baru": harga_jual_baru,

                "warning": "; ".join(warning)
                    if warning
                    else "-"
            })

        # ==========================================
        # DATA BARU
        # ==========================================

        else:

            new_data.append({

                "merk": row["merk"],
                "kode": row["kode"],
                "distributor": row["distributor"],
                "harga_modal": row["harga_modal"],
                "harga_jual": row["harga_jual"],
                "stock": row["stock"]

            })

    return (
        pd.DataFrame(update_data),
        pd.DataFrame(new_data)
    )


# ==================================================
# UPDATE / INSERT FRAME
# ==================================================

def update_frames(
    df_update,
    df_new,
    user="Unknown"
):

    supabase = get_supabase()

    updated = []
    inserted = []

    # ==================================================
    # UPDATE FRAME EXISTING
    # ==================================================

    for _, row in df_update.iterrows():

        update_data = {
            "stock": row["stock_akhir"],
            "harga_modal": row["harga_modal_baru"],
            "harga_jual": row["harga_jual_baru"]
        }

        # ------------------------------------------
        # UPDATE DISTRIBUTOR
        # ------------------------------------------

        if pd.notna(row["distributor_baru"]):

            update_data["distributor"] = (
                row["distributor_baru"]
            )

        # ------------------------------------------
        # UPDATE DATABASE
        # ------------------------------------------

        response = (
            supabase
            .table("frames")
            .update(update_data)
            .eq("id", row["id"])
            .execute()
        )

        if not response.data:

            raise Exception(
                f"Gagal update frame "
                f"{row['merk']} - {row['kode']}"
            )

        # ------------------------------------------
        # SIMPAN LIST BERHASIL UPDATE
        # ------------------------------------------

        updated.append(
            (
                row["merk"],
                row["kode"]
            )
        )

        # ==========================================
        # LOG STOCK
        # ==========================================

        if row["stock_tambah"] != 0:

            log_frame_stock(
                merk=row["merk"],
                kode=row["kode"],
                jumlah_input=row["stock_tambah"],
                stock_lama=row["stock_lama"],
                stock_baru=row["stock_akhir"],
                user=user
            )

        # ==========================================
        # LOG DISTRIBUTOR
        # ==========================================

        distributor_berubah = (

            (
                pd.isna(row["distributor_lama"])
                and pd.notna(row["distributor_baru"])
            )

            or

            (
                pd.notna(row["distributor_lama"])
                and pd.notna(row["distributor_baru"])
                and
                row["distributor_lama"]
                != row["distributor_baru"]
            )
        )

        if distributor_berubah:

            log_frame_distributor(
                merk=row["merk"],
                kode=row["kode"],
                distributor_lama=row["distributor_lama"],
                distributor_baru=row["distributor_baru"],
                user=user
            )

        # ==========================================
        # LOG HARGA JUAL
        # ==========================================

        harga_berubah = (
            row["harga_jual_lama"]
            != row["harga_jual_baru"]
        )

        if harga_berubah:

            log_frame_harga(
                merk=row["merk"],
                kode=row["kode"],
                harga_lama=row["harga_jual_lama"],
                harga_baru=row["harga_jual_baru"],
                user=user
            )

    # ==================================================
    # INSERT FRAME BARU
    # ==================================================

    for _, row in df_new.iterrows():

        new_data = {

            "merk": row["merk"],
            "kode": row["kode"],
            "distributor": row["distributor"],
            "harga_modal": row["harga_modal"],
            "harga_jual": row["harga_jual"],
            "stock": row["stock"]

        }

        response = (
            supabase
            .table("frames")
            .insert(new_data)
            .execute()
        )

        if not response.data:

            raise Exception(
                f"Gagal insert frame "
                f"{row['merk']} - {row['kode']}"
            )

        # ------------------------------------------
        # SIMPAN LIST BERHASIL INSERT
        # ------------------------------------------

        inserted.append(
            (
                row["merk"],
                row["kode"]
            )
        )

        # ------------------------------------------
        # LOG FRAME BARU
        # ------------------------------------------

        log_frame_baru(
            merk=row["merk"],
            kode=row["kode"],
            stock=row["stock"],
            user=user
        )

    # ==================================================
    # RETURN HASIL
    # ==================================================

    return {
        "updated": updated,
        "inserted": inserted
    }