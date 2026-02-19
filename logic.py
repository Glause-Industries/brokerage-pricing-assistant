# logic.py
import pandas as pd
from io import BytesIO

def run_pricing_logic(file_bytes: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(BytesIO(file_bytes))

    lanes = pd.read_excel(xls, sheet_name="Sheet1")
    logic = pd.read_excel(xls, sheet_name="Logic Sheet", dtype={"3Zip": str})

    # === Clean logic sheet ===
    if "Group" not in logic.columns:
        logic["Group"] = "Neutral"
    if "Do_Not_Price" not in logic.columns:
        logic["Do_Not_Price"] = logic["Group"].eq("DoNotPrice").map(
            {True: "YES", False: "NO"}
        )
    if "OB_Status" not in logic.columns:
        logic["OB_Status"] = "NEUTRAL"
    if "IB_Status" not in logic.columns:
        logic["IB_Status"] = "NEUTRAL"

    priority_order = {"DoNotPrice": 1, "LOI": 2, "Neutral": 3}
    logic["Priority"] = logic["Group"].map(priority_order).fillna(3)
    logic_sorted = logic.sort_values(["3Zip", "Priority"])
    zip_unique = logic_sorted.groupby("3Zip", as_index=False).first()
    zip_map = zip_unique.set_index("3Zip").to_dict(orient="index")

    # === Scope lanes: Division V, MIDWEST/WEST, RPM > 0 ===
    v_mask = lanes["Division"] == "V"
    office_mask = lanes["Brokerage Office"].isin(["MIDWEST", "WEST"])
    rated_mask = lanes["Brokerage Proposed RPM"].notna() & (lanes["Brokerage Proposed RPM"] > 0)

    scoped = lanes[v_mask & office_mask & rated_mask].copy()

    # === Build notes ===
    notes = []
    for _, row in scoped.iterrows():
        oz3 = str(row.get("Origin 3Zip", "")) if pd.notna(row.get("Origin 3Zip")) else ""
        dz3 = str(row.get("Destination 3Zip", "")) if pd.notna(row.get("Destination 3Zip")) else ""
        oz3 = oz3[:3]
        dz3 = dz3[:3]

        o_meta = zip_map.get(oz3)
        d_meta = zip_map.get(dz3)

        note = ""

        # Do-not-price overrides
        if o_meta and o_meta.get("Do_Not_Price") == "YES":
            note = f"Not priced - {o_meta.get('Metro_Name')}"
        elif d_meta and d_meta.get("Do_Not_Price") == "YES":
            note = f"Not priced - {d_meta.get('Metro_Name')}"

        # LOI pairing
        if note == "" and o_meta and d_meta:
            if o_meta.get("OB_Status") == "LOI" and d_meta.get("IB_Status") == "LOI":
                o_abbr = o_meta.get("Abbrev") or ""
                d_abbr = d_meta.get("Abbrev") or ""
                note = f"LOI - {o_abbr}-{d_abbr}"

        notes.append(note)

    scoped["My_Pricing_Notes"] = notes

    cols = [
        "Customer Order",
        "Origin City",
        "Origin State",
        "Origin 3Zip",
        "Destination City",
        "Destination State",
        "Destination 3Zip",
        "Customer Loads / Year",
        "Origin Live/Drop",
        "Destination Live/Drop",
        "Brokerage Proposed RPM",
        "Brokerage Proposed RPL",
        "Brokerage Office",
        "My_Pricing_Notes",
    ]

    export_df = scoped[cols].sort_values("Customer Order")
    return export_df
