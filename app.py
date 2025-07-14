import streamlit as st
import pandas as pd
from scheduler import generate_schedule
from datetime import date
from io import BytesIO

st.set_page_config(page_title="COSMOS Onboarding Assistant", layout="wide")

st.title("👥 COSMOS Onboarding Assistant")

uploaded_file = st.file_uploader(
    "📂 Upload Training Program.xlsx (must contain sheet ‘Final Template’)",
    type=["xlsx"]
)

if uploaded_file:
    try:
        # ▸ Read ONLY the ‘Final Template’ sheet
        df_template = pd.read_excel(uploaded_file, sheet_name="Final Template")
    except Exception as e:
        st.error(f"❌ Cannot find sheet ‘Final Template’. Error: {e}")
        st.stop()

    # ▸ Populate roles from the column
    roles = sorted(df_template["Role"].dropna().unique())
    role = st.selectbox("🧑‍💼 Role", roles)

    st.subheader("🧍 Newcomer Info")
    newcomer_name = st.text_input("Full Name")
    newcomer_email = st.text_input("Email")

    hire_date = st.date_input("Start Date", value=date.today())

    st.subheader("👔 Manager Info")
    mgr1_name = st.text_input("Manager 1 Name")
    mgr1_email = st.text_input("Manager 1 Email")
    add_mgr2 = st.checkbox("Add Manager 2?")
    mgr2_name = mgr2_email = ""
    if add_mgr2:
        mgr2_name = st.text_input("Manager 2 Name")
        mgr2_email = st.text_input("Manager 2 Email")

    if st.button("📅 Generate Schedule"):
        # Basic validation
        if not (newcomer_name and newcomer_email and mgr1_name and mgr1_email):
            st.warning("Fill newcomer + Manager 1 fields.")
            st.stop()

        schedule_df = generate_schedule(
            df_template, role, hire_date,
            newcomer_name, newcomer_email,
            mgr1_name, mgr1_email,
            mgr2_name, mgr2_email
        )

        st.success("✅ Schedule generated!")
        st.dataframe(schedule_df, use_container_width=True)

        # Download as Excel
        buffer = BytesIO()
        schedule_df.to_excel(buffer, index=False)
        st.download_button(
            "⬇️ Download Excel",
            buffer.getvalue(),
            file_name=f"{newcomer_name.replace(' ', '_')}_schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Upload your Excel file to begin.")
