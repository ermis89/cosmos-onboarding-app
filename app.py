import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(layout="wide")
st.title("📅 COSMOS Onboarding Assistant")

st.markdown("### 📤 Upload your Excel template")
uploaded_file = st.file_uploader("Choose your onboarding Excel file", type=["xlsx"])

if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names
    sheet_name = st.selectbox("📄 Select Sheet", sheet_names)
    df_template = xl.parse(sheet_name)
    
    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 Επιλέξτε Ρόλο (Select Role)", roles)
    start_date = st.date_input("📅 Ημερομηνία Έναρξης (Start Date)")
    
    st.markdown("### 🧍‍♂️ Newcomer Info")
    newcomer_name = st.text_input("Full Name")
    newcomer_email = st.text_input("Email")

    st.markdown("### 🧑‍💼 Manager Info")
    manager1_name = st.text_input("Manager 1 Name")
    manager1_email = st.text_input("Manager 1 Email")
    add_manager2 = st.checkbox("➕ Add Manager 2?")
    manager2_name = manager2_email = ""
    if add_manager2:
        manager2_name = st.text_input("Manager 2 Name")
        manager2_email = st.text_input("Manager 2 Email")

    if st.button("📅 Δημιουργία Προγράμματος / Generate Schedule"):
        with st.spinner("Generating schedule..."):
            schedule_df = generate_schedule(
                df_template, role, start_date, newcomer_name, newcomer_email,
                manager1_name, manager1_email, manager2_name, manager2_email
            )
            st.success("✅ Schedule generated!")
            st.dataframe(schedule_df)
            csv = schedule_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ Download Schedule", csv, file_name=f"{newcomer_name.replace(' ', '_')}_schedule.csv", mime='text/csv')
