import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👥 COSMOS Onboarding Assistant")
st.markdown("Καλωσήρθατε! Upload το αρχείο σας, επιλέξτε ρόλο και ημερομηνία έναρξης για να δημιουργήσετε το πρόγραμμα ένταξης. (Welcome! Upload your file and select a role/date to generate the onboarding schedule.)")

uploaded_file = st.file_uploader("📁 Επιλέξτε το Excel αρχείο προτύπου (Choose your onboarding Excel template)", type=["xlsx"])

if uploaded_file:
    df_template = pd.read_excel(uploaded_file, sheet_name="Final Template")
    roles = df_template["Role"].dropna().unique()
    role = st.selectbox("🧑‍💼 Επιλέξτε Ρόλο (Select Role)", sorted(roles))
    name = st.text_input("👤 Όνομα Νεοπροσλαμβανόμενου (New hire full name)")
    hire_date = st.date_input("📅 Ημερομηνία Έναρξης (Start Date)")

    if st.button("📆 Δημιουργία Προγράμματος / Generate Schedule"):
        filtered = df_template[df_template["Role"] == role].sort_values("Order")
        rdvs = filtered.to_dict(orient="records")
        schedule_df = generate_schedule(hire_date.strftime("%d/%m/%Y"), rdvs)
        st.success("✅ Το πρόγραμμα δημιουργήθηκε! (Schedule generated!)")
        st.dataframe(schedule_df, use_container_width=True)

        csv = schedule_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("💾 Κατέβασμα ως CSV / Download as CSV", csv, file_name=f"{name}_schedule.csv")
