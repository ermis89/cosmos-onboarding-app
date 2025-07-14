import streamlit as st
import pandas as pd
from scheduler import generate_schedule
import io

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("📥 Καλωσήρθατε! Upload το αρχείο σας για να δημιουργήσετε πρόγραμμα ένταξης")

uploaded_file = st.file_uploader("📑 Επιλέξτε το Excel αρχείο προτύπου", type="xlsx")

if uploaded_file:
    sheet_names = pd.ExcelFile(uploaded_file).sheet_names
    selected_sheet = st.selectbox("📋 Επιλέξτε φύλλο (Select Sheet)", sheet_names)
    
    df_template = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
    
    # Dynamically extract available roles
    available_roles = df_template["Role"].dropna().unique()
    selected_role = st.selectbox("🎓 Επιλέξτε Ρόλο (Select Role)", available_roles)

    st.subheader("🧍 Newcomer Info")
    newcomer_name = st.text_input("Full Name", placeholder="e.g. Andreadakis Giannis")
    newcomer_email = st.text_input("Email", placeholder="e.g. andreadakisg@cbs.gr")
    start_date = st.date_input("Start Date")

    st.subheader("👔 Manager Info")
    manager1_name = st.text_input("Manager 1 Name", placeholder="e.g. Vassilikos Peter")
    manager1_email = st.text_input("Manager 1 Email", placeholder="e.g. vassilikosp@cbs.gr")
    
    add_second_manager = st.checkbox("➕ Add Manager 2?")
    manager2_name = ""
    manager2_email = ""
    if add_second_manager:
        manager2_name = st.text_input("Manager 2 Name (optional)")
        manager2_email = st.text_input("Manager 2 Email (optional)")

    if st.button("📅 Generate Schedule / Δημιουργία Προγράμματος"):
        if not selected_role or not newcomer_name or not newcomer_email:
            st.error("⚠️ Please fill in all required fields.")
        else:
            schedule_df = generate_schedule(
                df_template,
                selected_role,
                start_date,
                newcomer_name,
                newcomer_email,
                manager1_name,
                manager1_email,
                manager2_name,
                manager2_email,
            )
            if schedule_df.empty:
                st.error("❌ No schedule generated. Please check role name or Excel data.")
            else:
                st.success("✅ Schedule generated!")
                st.dataframe(schedule_df)

                csv = schedule_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{newcomer_name.replace(' ', '_')}_schedule.csv",
                    mime="text/csv",
                )
