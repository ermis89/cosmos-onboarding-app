import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.markdown("## 👥 COSMOS Onboarding Assistant")
st.markdown("Καλωσήρθατε! Upload το αρχείο σας, επιλέξτε ρόλο και ημερομηνία έναρξης για να δημιουργήσετε το πρόγραμμα ένταξης. (Welcome! Upload your file and select a role/date to generate the onboarding schedule.)")

uploaded_file = st.file_uploader("📂 Επιλέξτε το Excel αρχείο προτύπου (Choose your onboarding Excel template)", type=["xlsx"])

if uploaded_file:
    try:
        df_template = pd.read_excel(uploaded_file, sheet_name="Final Template")
        roles = sorted(df_template["Role"].dropna().unique())
    except Exception as e:
        st.error(f"⚠️ Could not read sheet 'Final Template'. Error: {e}")
        st.stop()

    role = st.selectbox("🧑‍💼 Επιλέξτε Ρόλο (Select Role)", roles)
    newcomer_name = st.text_input("🧑‍🤝‍🧑 Όνομα Νεοπροσλαμβανόμενου (New hire full name)")
    newcomer_email = st.text_input("📧 Email Νεοπροσλαμβανόμενου (New hire email)")

    start_date = st.date_input("🗓️ Ημερομηνία Έναρξης (Start Date)")

    with st.expander("👥 Πληροφορίες Υπευθύνων (Manager Info)", expanded=True):
        manager1_name = st.text_input("👤 Manager 1 Name")
        manager1_email = st.text_input("📧 Manager 1 Email")
        manager2_name = st.text_input("👤 Manager 2 Name (optional)", "")
        manager2_email = st.text_input("📧 Manager 2 Email (optional)", "")

    if st.button("🗓️ Δημιουργία Προγράμματος / Generate Schedule"):
        if not newcomer_name or not newcomer_email or not role:
            st.warning("⚠️ Please fill in all required fields.")
        else:
            schedule_df = generate_schedule(
                df_template, role, start_date, newcomer_name, newcomer_email,
                manager1_name, manager1_email, manager2_name, manager2_email
            )
            st.success("✅ Schedule generated!")

            st.dataframe(schedule_df, use_container_width=True)

            csv = schedule_df.to_csv(index=False).encode("utf-8-sig")
            filename = f"{newcomer_name.replace(' ', '_')}_schedule.csv"
            st.download_button("📥 Download Schedule as CSV", data=csv, file_name=filename, mime="text/csv")
