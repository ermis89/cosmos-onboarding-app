import streamlit as st
import pandas as pd
from datetime import date
from scheduler import generate_schedule, merge_manual_rdvs

st.set_page_config(layout="wide")
st.title("📅 COSMOS Onboarding Assistant")

# ────────────────────────────────────────────────────────────────
# 1. Upload template (first row already contains headers)
# ────────────────────────────────────────────────────────────────
xlsx_file = st.file_uploader(
    "Upload Training Program.xlsx (sheet ‘Final Template’). First row must be headers.",
    type=["xlsx", "xls"]
)
if not xlsx_file:
    st.stop()

try:
    df_template = pd.read_excel(xlsx_file, sheet_name="Final Template", header=0)
    df_template.columns = df_template.columns.str.strip()          # trim spaces
except Exception as e:
    st.exception(e)
    st.stop()

if "Role" not in df_template.columns:
    st.error(f"'Role' column not found. Detected columns: {list(df_template.columns)}")
    st.stop()

# ensure Duration numeric
if "Duration" in df_template.columns:
    df_template["Duration"] = pd.to_numeric(df_template["Duration"], errors="coerce")

# roles list
roles = sorted(df_template["Role"].dropna().unique())
role = st.selectbox("Role", roles)

# ───── newcomer & manager fields ────────────────────────────────
st.subheader("Newcomer Info")
newcomer_name  = st.text_input("Newcomer Name")
newcomer_email = st.text_input("Newcomer Email")
start_date     = st.date_input("Hire Date", value=date.today())

st.subheader("Manager Info")
mgr1_name  = st.text_input("Manager 1 Name")
mgr1_email = st.text_input("Manager 1 Email")
add_mgr2   = st.checkbox("Add Manager 2?")
mgr2_name  = st.text_input("Manager 2 Name",  disabled=not add_mgr2)
mgr2_email = st.text_input("Manager 2 Email", disabled=not add_mgr2)

# ───── manager‑priority RDVs table ──────────────────────────────
st.subheader("Manager Changes (priority RDVs)")
default_row = {
    "Date":        start_date,
    "Start":       "09:00",
    "End":         "09:30",
    "Location":    "",
    "Title":       "",
    "Description": "",
    "C1 Name":     "", "C1 Email": "",
    "C2 Name":     "", "C2 Email": ""
}
if "manual_rdvs" not in st.session_state:
    st.session_state.manual_rdvs = pd.DataFrame([default_row])

edited_df = st.data_editor(
    st.session_state.manual_rdvs,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="editor",
)
if st.button("💾 Save changes"):
    st.session_state.manual_rdvs = edited_df.copy()
    st.success("Changes saved!")

# ───── generate schedule ───────────────────────────────────────
if st.button("📅 Generate Schedule"):

    st.session_state.manual_rdvs = edited_df.copy()  # capture latest edits

    if not all([newcomer_name, newcomer_email, mgr1_name, mgr1_email]):
        st.warning("Please fill newcomer & Manager‑1 info.")
        st.stop()

    # clean manual table
    manual_clean = (st.session_state.manual_rdvs
                    .dropna(how="all")
                    .query("Start.str.strip() != '' or End.str.strip() != '' or Title.str.strip() != ''",
                           engine="python"))

    # validate mandatory fields
    bad_rows = manual_clean[
        manual_clean["Date"].isna() |
        (manual_clean["Start"].str.strip() == "") |
        (manual_clean["End"].str.strip()   == "") |
        (manual_clean["Title"].str.strip() == "")
    ]
    if not bad_rows.empty:
        st.warning("Every manual RDV row needs Date, Start, End and Title.")
        st.stop()

    # build schedules
    try:
        auto_df = generate_schedule(
            df_template, role, start_date,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )
        final_df = merge_manual_rdvs(
            auto_df, manual_clean,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )

    # ⬇️ NEW — show what auto‑scheduler produced
    st.write("🔍 Auto‑scheduler rows:", len(auto_df))
    st.write(auto_df.head())

    final_df = merge_manual_rdvs(
        auto_df, manual_clean,
        newcomer_name, newcomer_email,
        mgr1_name, mgr1_email,
        mgr2_name, mgr2_email
    )
    # ⬇️ NEW — show rows after merging manual RDVs
    st.write("🔍 Final rows after merge:", len(final_df))
    st.write(final_df.head())
    
    except Exception as e:
        st.exception(e)
        st.stop()

    if final_df.empty:
        st.error("No RDVs generated — check template or overlaps.")
        st.stop()

    st.success("✅ Final schedule created!")
    st.dataframe(final_df, use_container_width=True)
    csv = final_df.to_csv(index=False).encode("utf-8-sig")
    fname = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
    st.download_button("⬇️ Download CSV", csv, file_name=fname, mime="text/csv")
