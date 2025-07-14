import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👥 COSMOS Onboarding Assistant")
st.markdown(
    """
    **Καλωσήρθατε!**  \n
    1. **Ανεβάστε** το αρχείο Excel `Training Program.xlsx`  \n
    2. **Επιλέξτε** ρόλο, συμπληρώστε **όνομα** & **ημερομηνία πρόσληψης**  \n
    3. Πατήστε **«Δημιουργία Προγράμματος / Generate Schedule»**  \n
    ---
    """
)

# 1 ▸ Upload Excel
uploaded_file = st.file_uploader(
    "📁 **Επιλέξτε το Excel αρχείο προτύπου**  (Choose your onboarding Excel template)",
    type=["xlsx"],
)

if uploaded_file:
    try:
        df_template = pd.read_excel(uploaded_file, sheet_name="Final Template")
    except Exception as e:
        st.error(f"❌ Δεν μπορώ να διαβάσω το φύλλο ‘Final Template’. Error: {e}")
        st.stop()

    # 2 ▸ User inputs
    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 **Επιλέξτε Ρόλο (Select Role)**", roles)

    name = st.text_input("👤 **Όνομα Νεοπροσλαμβανόμενου (New hire full name)**")

    hire_date = st.date_input("📅 **Ημερομηνία Έναρξης (Start Date)**")

    # 3 ▸ Button
    if st.button("📆 Δημιουργία Προγράμματος / Generate Schedule"):
        if not name:
            st.warning("⚠️ Συμπληρώστε όνομα νεοπροσλαμβανόμενου. (Please enter the new hire’s name.)")
            st.stop()

        # Filter RDVs for chosen role
        rdvs = (
            df_template[df_template["Role"] == role]
            .sort_values("Order")
            .to_dict(orient="records")
        )

        # Create schedule
        schedule_df = generate_schedule(hire_date.strftime("%d/%m/%Y"), rdvs)

        if schedule_df.empty:
            st.error("❌ Δεν βρέθηκαν RDVs για τον ρόλο αυτό. (No RDVs found for this role.)")
            st.stop()

        # Display
        st.success("✅ Το πρόγραμμα δημιουργήθηκε! (Schedule generated!)")
        st.dataframe(schedule_df, use_container_width=True)

        # Download
        csv = schedule_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "💾 Κατέβασμα ως CSV / Download as CSV",
            csv,
            file_name=f"{name.replace(' ', '_')}_schedule.csv",
            mime="text/csv",
        )
else:
    st.info("⬆️ Ανεβάστε το Excel για να ξεκινήσετε. (Upload an Excel file to begin.)")
