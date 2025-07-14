import streamlit as st
import pandas as pd
from scheduler import generate_schedule

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👥 COSMOS Onboarding Assistant")
st.markdown(
    """
    **Καλωσήρθατε!**  \n
    1. **Upload** the Excel template  \n
    2. **Fill** newcomer, role, managers & hire date  \n
    3. Click **Generate Schedule**  \n
    ---
    """
)

uploaded_file = st.file_uploader(
    "📁 **Upload Excel template** (`Training Program.xlsx`)", type=["xlsx"]
)

if uploaded_file:
    try:
        df_template = pd.read_excel(uploaded_file, sheet_name="Final Template")
    except Exception as e:
        st.error(f"❌ Cannot read sheet ‘Final Template’. Error: {e}")
        st.stop()

    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 **Role**", roles)

    name = st.text_input("👤 **Newcomer Name**")
    email = st.text_input("📧 **Newcomer Email**")

    hire_date = st.date_input("📅 **Hire Start Date**")

    st.subheader("👔 Managers")
    mgr1_name = st.text_input("Manager 1 Name", key="mgr1n")
    mgr1_email = st.text_input("Manager 1 Email", key="mgr1e")
    mgr2_name = st.text_input("Manager 2 Name (optional)", key="mgr2n")
    mgr2_email = st.text_input("Manager 2 Email (optional)", key="mgr2e")

    if st.button("📆 Δημιουργία Προγράμματος / Generate Schedule"):
        # basic validation
        if not (name and email and mgr1_name and mgr1_email):
            st.warning("⚠️ Please fill newcomer & first-manager info.")
            st.stop()

        rdvs = (
            df_template[df_template["Role"] == role]
            .sort_values("Order")
            .to_dict(orient="records")
        )

        schedule = generate_schedule(hire_date.strftime("%d/%m/%Y"), rdvs)

        # add newcomer + manager columns
        schedule["Newcomer Name"] = name
        schedule["Newcomer Email"] = email
        schedule["Manager1 Name"] = mgr1_name
        schedule["Manager1 Email"] = mgr1_email
        schedule["Manager2 Name"] = mgr2_name
        schedule["Manager2 Email"] = mgr2_email
        schedule["Hired Date"] = hire_date.strftime("%Y-%m-%d")
        schedule["Status"] = "Scheduled"

        # reorder according to your template
        order_cols = [
            "Newcomer Email", "Newcomer Name", "Role",        # Role ~ Role Group
            "RDV", "Short RDV Description",
            "Contact Person1 Email", "Contact Person1 Name",
            "Contact Person2 Email", "Contact Person2 Name",
            "Day", "Start Time", "End Time", "Duration (minutes)",
            "Location",
            "Manager1 Email", "Manager1 Name",
            "Manager2 Email", "Manager2 Name",
            "Status", "Hired Date",
            "Order",
        ]
        schedule = schedule.reindex(columns=order_cols)

        st.success("✅ Schedule generated!")
        st.dataframe(schedule, use_container_width=True)

        csv = schedule.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "💾 Download CSV",
            csv,
            file_name=f"{name.replace(' ', '_')}_schedule.csv",
            mime="text/csv",
        )
else:
    st.info("⬆️ Upload an Excel file to start.")
