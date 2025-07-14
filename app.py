
import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👋 Καλωσήρθατε! Upload το αρχείο σας, επιλέξτε ρόλο και ημερομηνία έναρξης για να δημιουργήσετε το πρόγραμμα ένταξης.")
uploaded_file = st.file_uploader("📂 Επιλέξτε το Excel αρχείο προτύπου (Choose your onboarding Excel template)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    selected_sheet = st.selectbox("📄 Επιλέξτε Ρόλο (Select Role)", sheet_names)
    df_template = pd.read_excel(xls, sheet_name=selected_sheet)

    st.subheader("🧍‍♂️ Newcomer Info")
    newcomer_name = st.text_input("Full Name", placeholder="e.g. Andreadakis Giannis")
    newcomer_email = st.text_input("Email", placeholder="e.g. andreadakiscbs@gmail.com")
    start_date = st.date_input("Start Date")

    st.subheader("👔 Manager Info")
    manager1_name = st.text_input("Manager 1 Name", placeholder="e.g. Vassilikos Peter")
    manager1_email = st.text_input("Manager 1 Email", placeholder="e.g. vassilikosp@cbs.gr")
    add_manager2 = st.checkbox("➕ Add Manager 2?")
    manager2_name = manager2_email = ""
    if add_manager2:
        manager2_name = st.text_input("Manager 2 Name", placeholder="Optional")
        manager2_email = st.text_input("Manager 2 Email", placeholder="Optional")

    if st.button("🗓️ Generate Schedule / Δημιουργία Προγράμματος"):
        schedule_df = generate_schedule(
            df_template, selected_sheet, start_date, newcomer_name, newcomer_email,
            manager1_name, manager1_email, manager2_name, manager2_email
        )
        st.success("✅ Schedule generated!")
        st.dataframe(schedule_df)
        csv = schedule_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download CSV", csv, f"{newcomer_name.replace(' ', '_')}_schedule.csv", "text/csv")
