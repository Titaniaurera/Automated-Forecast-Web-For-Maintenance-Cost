import os
import json


# =====================================================
# TABEL ACUAN SATUAN (MATERIAL -> UNIT OF ENTRY)
#
# Sumber: data GR
# Dipakai oleh: GR, stock, projection
# =====================================================


DATA_FOLDER = "data"

UNIT_FILE = os.path.join(

    DATA_FOLDER,

    "material_unit.json"

)


os.makedirs(

    DATA_FOLDER,

    exist_ok=True

)


# =====================================================
# LOAD
# =====================================================


def load_material_unit_map():

    if not os.path.exists(UNIT_FILE):

        return {}

    try:

        with open(

            UNIT_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            return json.load(f)

    except Exception:

        return {}


# =====================================================
# SAVE
#
# Digabung dengan data lama:
# - material baru ditambah
# - material lama yang satuannya berubah ikut diperbarui
# - material lama yang tidak ada di upload baru tetap aman
# =====================================================


def save_material_unit_map(new_map):

    merged = load_material_unit_map()

    merged.update(new_map)

    tmp_file = UNIT_FILE + ".tmp"

    with open(

        tmp_file,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            merged,

            f,

            ensure_ascii=False

        )

    os.replace(

        tmp_file,

        UNIT_FILE

    )

    return merged