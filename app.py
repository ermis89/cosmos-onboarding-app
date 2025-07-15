import streamlit as st
import pandas as pd
from datetime import datetime
from scheduler import generate_schedule, merge_manual_rdvs

st.set_page_config(layout="wide")
st.title("📅 COSMOS Onboarding Assistant")

# 1. Upload template
st.subheader("1. Upload RDV Template Excel")
template_file = st.file_uploader("Upload Excel", type=["xlsx"])
if not template_file:
    st.stop()

df_template = pd.read_excel(template_file)
roles = df_template["Role"].dropna().unique().tolist()

# 2. Newcomer Info
st.subheader("2. Newcomer Info")
col1, col2 = st.columns(2)
newcomer_name = col1.text_input("Newcomer Name")
newcomer_email = col2.text_input("Newcomer Email")

col3, col4 = st.columns(2)
role = col3.selectbox("Role", roles)
start_date = col4.date_input("Hire Date", datetime.today())

# 3. Manager info
st.subheader("3. Managers Info")
mgr1_name = st.text_input("Manager 1 Name")
mgr1_email = st.text_input("Manager 1 Email")
mgr2_name = st.text_input("Manager 2 Name (optional)", "")
mgr2_email = st.text_input("Manager 2 Email (optional)", "")

# 4. Manual RDV overrides
st.subheader("4. Manager Changes (priority RDVs)")

default_row = {
    "Date": datetime.today().date(),
    "Start": "09:00",
    "End": "09:30",
    "Location": "",
    "Title": "",
    "Description": "",
    "C1 Name": "", "C1 Email": "",
    "C2 Name": "", "C2 Email": ""
}

if "manual_rdvs" not in st.session_state:
    st.session_state.manual_rdvs = pd.DataFrame([default_row])

edited_df = st.data_editor(
    st.session_state.manual_rdvs,
    use_container_width=True,
    num_rows="dynamic",
    key="editor"
)

if st.button("💾 Save changes"):
    st.session_state.manual_rdvs = edited_df.copy()
    st.success("Changes saved!")

# 5. Generate schedule
st.subheader("5. Generate Schedule")

if st.button("📅 Generate Schedule"):

    if not all([newcomer_name, newcomer_email, mgr1_name, mgr1_email]):
        st.warning("Please fill newcomer & Manager‑1 info.")
        st.stop()

    # overwrite in case Save not pressed
    st.session_state.manual_rdvs = edited_df.copy()

    # clean manual table
    manual_clean = st.session_state.manual_rdvs.dropna(how="all")
    manual_clean = manual_clean[
        (manual_clean["Start"].str.strip() != "") |
        (manual_clean["End"].str.strip() != "") |
        (manual_clean["Title"].str.strip() != "")
    ]

    # check required fields
    bad_rows = manual_clean[
        manual_clean["Date"].isna() |
        (manual_clean["Start"].str.strip() == "") |
        (manual_clean["End"].str.strip() == "") |
        (manual_clean["Title"].str.strip() == "")
    ]
    if not bad_rows.empty:
        st.warning("Each manual RDV must have Date, Start, End and Title.")
        st.stop()

    # debug
    st.write("✅ Manual rows after cleaning:", manual_clean)

    # build schedule
    try:
        sched_df = generate_schedule(
            df_template, role, start_date,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )
        final_df = merge_manual_rdvs(
            sched_df, manual_clean,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )
    except Exception as e:
        st.exception(e)
        st.stop()

    if final_df.empty:
        st.error("❌ No RDVs were generated. Check the role or time overlap.")
        st.stop()

    # success
    st.success("✅ Final schedule created!")
    st.dataframe(final_df, use_container_width=True)
    csv = final_df.to_csv(index=False).encode("utf-8-sig")
    filename = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
    st.download_button("⬇️ Download CSV", csv, file_name=filename, mime="text/csv")
