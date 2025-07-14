import pandas as pd

def generate_schedule(df, role, start_date, newcomer_name, newcomer_email, manager1_name, manager1_email, manager2_name, manager2_email):
    df_role = df[df["Role"] == role].copy()

    # Keep the original Excel row order
    schedule_rows = []
    rdv_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")

    for _, row in df_role.iterrows():
        schedule_rows.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name": newcomer_name,
            "Role Group": role,
            "RDV Title": row.get("RDV", ""),
            "RDV Description": row.get("Short RDV Description", ""),
            "Contact Person1 Email": row.get("Contact Person1 Email", ""),
            "Contact Person1 Name": row.get("Contact Person1 Name", ""),
            "Contact Person2 Email": row.get("Contact Person2 Email", ""),
            "Contact Person2 Name": row.get("Contact Person2 Name", ""),
            "RDV Date": rdv_date,
            "Start Time": row.get("Start Time", ""),
            "End Time": row.get("End Time", ""),
            "Duration": row.get("Duration", ""),
            "Location": row.get("Location", ""),
            "Manager1 Email": manager1_email,
            "Manager1 Name": manager1_name,
            "Manager2 Email": manager2_email,
            "Manager2 Name": manager2_name,
            "Status": "Planned",
            "Hired Date": rdv_date
        })

    return pd.DataFrame(schedule_rows)
