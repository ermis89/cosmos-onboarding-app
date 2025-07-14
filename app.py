import streamlit as st
import pandas as pd
from scheduler import generate_schedule
from datetime import date
from io import BytesIO

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")
st.title("📥 COSMOS Onboarding Assistant")

# ──────────────────────────── Upload Excel
xlsx_file = st.file_uploader("Upload Training Program.xlsx", type="xlsx")

if xlsx_file:
    try:
        df_template = pd.read_excel(xlsx_file, sheet_name="Final Template")
    except ValueError:
        st.error("❌ Sheet ‘Final Template’ was not found in the workbook.")
        st.stop()

    # ──────────────────────────── Role dropdown
    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 Select Role", roles)

    # ──────────────────────────── New-hire & manager info
    st.subheader("Newcomer Info")
    newcomer_name  = st.text_input("Full Name")
    newcomer_email = st.text_input("Email")

    start_date = st.date_input("Start Date", value=date.today())

    st.subheader("Manager Info")
    mgr1_name  = st.text_input("Manager 1 Name")
    mgr1_email = st.text_input("Manager 1 Email")
    add_mgr2   = st.checkbox("Add Manager 2?")
    mgr2_name  = st.text_input("Manager 2 Name",  disabled=not add_mgr2)
    mgr2_email = st.text_input("Manager 2 Email", disabled=not add_mgr2)

    # ──────────────────────────── Generate schedule
    if st.button("📅 Generate Schedule"):
        required = [newcomer_name, newcomer_email, mgr1_name, mgr1_email, role]
        if not all(required):
            st.warning("Please fill newcomer info, Manager 1, and select a role.")
            st.stop()

        sched_df = generate_schedule(
            df_template, role, start_date,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email, mgr2_name, mgr2_email
        )

        st.success("✅ Schedule generated!")
        st.dataframe(sched_df, use_container_width=True)

        # CSV download
        csv = sched_df.to_csv(index=False).encode("utf-8-sig")
        fname = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
        st.download_button("⬇️ Download CSV", csv, file_name=fname, mime="text/csv")
