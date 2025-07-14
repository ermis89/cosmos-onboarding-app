import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👋 Καλωσήρθατε! Upload το αρχείο σας και επιλέξτε ρόλο και ημερομηνία έναρξης.")

uploaded_file = st.file_uploader("📄 Επιλέξτε το Excel αρχείο προτύπου", type=["xlsx"])
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    selected_sheet = st.selectbox("📑 Επιλέξτε Ρόλο", sheet_names)
    
    df_template = pd.read_excel(xls, sheet_name=selected_sheet)
    
    st.markdown("---")
    st.subheader("🧍 Newcomer Info")
    newcomer_name = st.text_input("Full Name")
    newcomer_email = st.text_input("Email")
    start_date = st.date_input("Start Date")

    st.subheader("👔 Manager Info")
    manager1_name = st.text_input("Manager 1 Name")
    manager1_email = st.text_input("Manager 1 Email")

    if st.checkbox("➕ Add Manager 2?"):
        manager2_name = st.text_input("Manager 2 Name (optional)")
        manager2_email = st.text_input("Manager 2 Email (optional)")
    else:
        manager2_name = ""
        manager2_email = ""

    if st.button("📅 Generate Schedule / Δημιουργία Προγράμματος"):
        if newcomer_name and newcomer_email and manager1_name and manager1_email:
            schedule_df = generate_schedule(
                df_template,
                selected_sheet,
                pd.to_datetime(start_date),
                newcomer_name,
                newcomer_email,
                manager1_name,
                manager1_email,
                manager2_name,
                manager2_email,
            )
            if not schedule_df.empty:
                st.success("✅ Schedule generated!")
                st.dataframe(schedule_df)
                csv = schedule_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Download CSV", csv, f"{newcomer_name}_schedule.csv", "text/csv")
            else:
                st.warning("⚠️ Schedule is empty. Check your inputs or template.")
        else:
            st.error("❌ Please fill all mandatory fields.")
