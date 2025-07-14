
import streamlit as st
import pandas as pd
from scheduler import generate_schedule
from io import BytesIO

st.set_page_config(page_title="COSMOS Onboarding Assistant", page_icon="👥", layout="wide")

st.title("👥 COSMOS Onboarding Assistant")
st.write("Καλωσήρθατε! Upload το αρχείο σας, επιλέξτε ρόλο και ημερομηνία έναρξης για να δημιουργήσετε το πρόγραμμα ένταξης. (Welcome! Upload your file and select a role/date to generate the onboarding schedule.)")

uploaded_file = st.file_uploader("📁 Επιλέξτε το Excel αρχείο προτύπου (Choose your onboarding Excel template)", type=["xlsx"])

if uploaded_file:
    df_dict = pd.read_excel(uploaded_file, sheet_name=None)
    roles = list(df_dict.keys())
    selected_role = st.selectbox("🧑‍💼 Επιλέξτε Ρόλο (Select Role)", roles)
    newcomer_name = st.text_input("👤 Όνομα Νεοπροσλαμβανόμενου (New hire full name)")
    newcomer_email = st.text_input("📧 Email Νεοπροσλαμβανόμενου (New hire email)")
    manager1_name = st.text_input("👔 Manager 1 Name")
    manager1_email = st.text_input("📧 Manager 1 Email")
    has_manager2 = st.checkbox("➕ Add second manager?")
    manager2_name = manager2_email = ""
    if has_manager2:
        manager2_name = st.text_input("👔 Manager 2 Name")
        manager2_email = st.text_input("📧 Manager 2 Email")
    start_date = st.date_input("📅 Ημερομηνία Έναρξης (Start Date)")

    if st.button("🗓️ Δημιουργία Προγράμματος / Generate Schedule"):
        rdvs = df_dict[selected_role]
        schedule = generate_schedule(
            start_date, rdvs.to_dict("records"),
            newcomer_name, newcomer_email,
            manager1_name, manager1_email,
            manager2_name, manager2_email
        )
        st.success("✅ Schedule generated!")
        st.dataframe(schedule)

        output = BytesIO()
        schedule.to_excel(output, index=False)
        st.download_button("📥 Λήψη σε Excel / Download Excel", output.getvalue(), file_name=f"{newcomer_name.replace(' ', '_')}_schedule.xlsx")
