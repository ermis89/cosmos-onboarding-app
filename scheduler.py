import pandas as pd
from datetime import datetime, timedelta

def generate_schedule(df, role, start_date, newcomer_name, newcomer_email, manager1_name, manager1_email, manager2_name, manager2_email):
    df_role = df[df["Role"] == role].copy()
    df_role = df_role.sort_values(by=["Day", "Order"])

    schedule_rows = []
    current_date = pd.to_datetime(start_date)
    hours = {
        1: ("10:00", "18:00"),  # First day
    }

    day_mapping = {}
    for _, row in df_role.iterrows():
        day = row["Day"]
        if day not in day_mapping:
            if day == 1:
                day_mapping[day] = current_date
            else:
                current_date += timedelta(days=1)
                day_mapping[day] = current_date

    for _, row in df_role.iterrows():
        rdv_date = day_mapping[row["Day"]]
        start_time = row["Start Time"]
        end_time = row["End Time"]

        schedule_rows.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name": newcomer_name,
            "Role Group": role,
            "RDV Title": row["RDV"],
            "RDV Description": row["Short RDV Description"],
            "Contact Person1 Email": row.get("Contact Person1 Email", ""),
            "Contact Person1 Name": row.get("Contact Person1 Name", ""),
            "Contact Person2 Email": row.get("Contact Person2 Email", ""),
            "Contact Person2 Name": row.get("Contact Person2 Name", ""),
            "RDV Date": rdv_date.strftime("%Y-%m-%d"),
            "Start Time": start_time,
            "End Time": end_time,
            "Duration": row["Duration"],
            "Location": row["Location"],
            "Manager1 Email": manager1_email,
            "Manager1 Name": manager1_name,
            "Manager2 Email": manager2_email,
            "Manager2 Name": manager2_name,
            "Status": "Planned",
            "Hired Date": pd.to_datetime(start_date).strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(schedule_rows)
