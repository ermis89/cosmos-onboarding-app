import streamlit as st
import pandas as pd
from scheduler import generate_schedule
from datetime import datetime

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👋 Καλωσήρθατε! Upload το αρχείο σας, επιλέξτε ρόλο και ημερομηνία έναρξης για να δημιουργήσετε το πρόγραμμα ένταξης. (Welcome! Upload your file and select a role/date to generate the onboarding schedule.)")

uploaded_file = st.file_uploader("📑 Επιλέξτε το Excel αρχείο προτύπου (Choose your onboarding Excel template)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    sheet = st.selectbox("🧾 Επιλέξτε Ρόλο (Select Role)", sheet_names)

    if sheet:
        df_template = pd.read_excel(xls, sheet_name=sheet)

        st.subheader("🧍 Πληροφορίες Νεοεισερχόμενου (Newcomer Info)")
        newcomer_name = st.text_input("👤 Όνομα Νεοεισερχόμενου / Newcomer Name")
        newcomer_email = st.text_input("📧 Email Νεοεισερχόμενου / Newcomer Email")

        start_date = st.date_input("📅 Ημερομηνία Έναρξης (Start Date)", format="YYYY/MM/DD")

        with st.expander("👥 Πληροφορίες Υπευθύνων (Manager Info)"):
            manager1_name = st.text_input("👤 Manager 1 Name", key="mgr1name")
            manager1_email = st.text_input("📧 Manager 1 Email", key="mgr1email")
            manager2_name = st.text_input("👤 Manager 2 Name (optional)", key="mgr2name")
            manager2_email = st.text_input("📧 Manager 2 Email (optional)", key="mgr2email")

        if st.button("📅 Δημιουργία Προγράμματος / Generate Schedule"):
            if not newcomer_name or not newcomer_email or not manager1_name or not manager1_email:
                st.error("❗ Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία (Please fill in all required fields).")
            else:
                schedule_df = generate_schedule(
                    df_template=df_template,
                    role=sheet,
                    hire_date=start_date,
                    newcomer_name=newcomer_name,
                    newcomer_email=newcomer_email,
                    mgr1_name=manager1_name,
                    mgr1_email=manager1_email,
                    mgr2_name=manager2_name,
                    mgr2_email=manager2_email
                )

                st.success("✅ Schedule generated!")
                st.dataframe(schedule_df, use_container_width=True)

                csv = schedule_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Schedule as CSV",
                    data=csv,
                    file_name=f"{newcomer_name.replace(' ', '_')}_schedule.csv",
                    mime="text/csv"
                )
