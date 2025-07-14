import streamlit as st
import pandas as pd
from scheduler import generate_schedule
from datetime import date, datetime

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")
st.title("📥 COSMOS Onboarding Assistant")

xlsx_file = st.file_uploader("Upload Training Program.xlsx (must contain sheet ‘Final Template’)", type="xlsx")

if xlsx_file:
    try:
        df_template = pd.read_excel(xlsx_file, sheet_name="Final Template")
        df_template["Duration"] = pd.to_numeric(df_template["Duration"], errors="raise")
    except ValueError:
        st.error("❌ Sheet ‘Final Template’ not found in workbook.")
        st.stop()
    except Exception as e:
        st.exception(e)
        st.stop()

    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 Select Role", roles)

    st.subheader("Newcomer Info")
    newcomer_name  = st.text_input("Full Name")
    newcomer_email = st.text_input("Email")
    start_date = st.date_input("Start Date", value=date.today())

    st.subheader("Manager Info")
    mgr1_name  = st.text_input("Manager 1 Name")
    mgr1_email = st.text_input("Manager 1 Email")
    add_mgr2 = st.checkbox("Add Manager 2?")
    mgr2_name = st.text_input("Manager 2 Name",  disabled=not add_mgr2)
    mgr2_email = st.text_input("Manager 2 Email", disabled=not add_mgr2)

    if st.button("📅 Generate Schedule"):
        if not all([newcomer_name, newcomer_email, mgr1_name, mgr1_email]):
            st.warning("Please fill newcomer + Manager 1 info.")
            st.stop()

        try:
            sched_df = generate_schedule(
                df_template, role, start_date,
                newcomer_name, newcomer_email,
                mgr1_name, mgr1_email, mgr2_name, mgr2_email
            )
        except Exception as e:
            st.exception(e)
            st.stop()

        if sched_df.empty:
            st.error("No RDVs found for selected role.")
            st.stop()

        st.success("✅ Schedule generated!")
        st.dataframe(sched_df, use_container_width=True)

        csv = sched_df.to_csv(index=False).encode("utf-8-sig")
        fn  = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
        st.download_button("⬇️ Download CSV", csv, file_name=fn, mime="text/csv")
