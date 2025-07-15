import streamlit as st
import pandas as pd
from datetime import date, datetime
from scheduler import generate_schedule, merge_manual_rdvs  # <- keep your scheduler

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")
st.title("📥 COSMOS Onboarding Assistant")

# ────────────────────────────────────────────────────────────────
# 1. Upload template
# ────────────────────────────────────────────────────────────────
xlsx_file = st.file_uploader(
    "Upload Training Program.xlsx (must contain sheet ‘Final Template’)",
    type="xlsx"
)

if not xlsx_file:
    st.stop()   # nothing else until file provided

try:
    df_template = pd.read_excel(xlsx_file, sheet_name="Final Template")
    df_template["Duration"] = pd.to_numeric(df_template["Duration"], errors="raise")
except ValueError:
    st.error("❌ Sheet ‘Final Template’ not found.")
    st.stop()
except Exception as e:
    st.exception(e)
    st.stop()

# ────────────────────────────────────────────────────────────────
# 2. Newcomer / manager inputs
# ────────────────────────────────────────────────────────────────
roles = sorted(df_template["Role"].dropna().unique())
role = st.selectbox("🧑‍💼 Select Role", roles)

st.subheader("Newcomer Info")
newcomer_name  = st.text_input("Full Name")
newcomer_email = st.text_input("Email")
start_date     = st.date_input("Start Date", value=date.today())

st.subheader("Manager Info")
mgr1_name  = st.text_input("Manager 1 Name")
mgr1_email = st.text_input("Manager 1 Email")
add_mgr2   = st.checkbox("Add Manager 2?")
mgr2_name  = st.text_input("Manager 2 Name",  disabled=not add_mgr2)
mgr2_email = st.text_input("Manager 2 Email", disabled=not add_mgr2)

# ────────────────────────────────────────────────────────────────
# 3. Manager‑priority RDVs table
# ────────────────────────────────────────────────────────────────
st.subheader("Manager Changes (priority RDVs)")

DEFAULT_ROW = {
    "Date":        start_date,
    "Start":       "09:00",
    "End":         "09:30",
    "Title":       "",
    "Description": "",
    "C1 Name":     "",
    "C1 Email":    "",
    "C2 Name":     "",
    "C2 Email":    ""
}

# first time in session, seed with one blank row
if "manual_rdvs" not in st.session_state:
    st.session_state.manual_rdvs = pd.DataFrame([DEFAULT_ROW])

with st.form("manual_form", clear_on_submit=False):
    edited_df = st.data_editor(
        st.session_state.manual_rdvs,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="manual_editor",
    )
    save_clicked = st.form_submit_button("💾 Save changes")

if save_clicked:
    st.session_state.manual_rdvs = edited_df
    st.success("Changes saved!")

# ────────────────────────────────────────────────────────────────
# 4. Generate schedule
# ────────────────────────────────────────────────────────────────
if st.button("📅 Generate Schedule"):

    # basic required fields
    if not all([newcomer_name, newcomer_email, mgr1_name, mgr1_email]):
        st.warning("Please fill newcomer & Manager‑1 info.")
        st.stop()

    # drop fully blank rows from manual table
    manual_clean = st.session_state.manual_rdvs.dropna(how="all")

    # validate required columns in manual rows
    bad_rows = manual_clean[
        manual_clean["Date"].isna() |
        (manual_clean["Start"].str.strip() == "") |
        (manual_clean["End"].str.strip() == "") |
        (manual_clean["Title"].str.strip() == "")
    ]
    if not bad_rows.empty:
        st.warning("Every manual RDV row needs Date, Start, End and Title.")
        st.stop()

    try:
        # auto schedule
        sched_df = generate_schedule(
            df_template, role, start_date,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )
        # merge manual priority rows
        final_df = merge_manual_rdvs(
            sched_df, manual_clean,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )

    except Exception as e:
        st.exception(e)
        st.stop()

    st.success("✅ Final schedule created!")
    st.dataframe(final_df, use_container_width=True)

    csv = final_df.to_csv(index=False).encode("utf-8-sig")
    filename = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
    st.download_button("⬇️ Download CSV", csv,
                       file_name=filename, mime="text/csv")
