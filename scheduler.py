import pandas as pd
from datetime import datetime, timedelta

def generate_schedule(
    df_template,
    role,
    start_date,
    newcomer_name,
    newcomer_email,
    manager1_name,
    manager1_email,
    manager2_name,
    manager2_email
):
    # Filter rows based on role
    df_role = df_template[df_template["Role"] == role].copy()
    if df_role.empty:
        return pd.DataFrame()  # Return empty if role not found

    df_role.reset_index(drop=True, inplace=True)

    schedule = []
    current_datetime = datetime.combine(start_date, datetime.strptime("10:00", "%H:%M").time())
    current_day = 1

    for idx, row in df_role.iterrows():
        rdv = row.get("RDV Title", "")
        description = row.get("RDV Description", "")
        duration = int(row.get("Duration", 60))
        location = row.get("Location", "")
        contact1_email = row.get("Contact Person1 Email", "None")
        contact1_name = row.get("Contact Person1 Name", "None")
        contact2_email = row.get("Contact Person2 Email", "None")
        contact2_name = row.get("Contact Person2 Name", "None")

        if "Break" in rdv:
            start_time = current_datetime
            end_time = start_time + timedelta(minutes=duration)
        else:
            start_time = current_datetime
            end_time = start_time + timedelta(minutes=duration)

        schedule.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name": newcomer_name,
            "Role": role,
            "RDV": rdv,
            "Short RDV Description": description,
            "Contact Person1 Email": contact1_email,
            "Contact Person1 Name": contact1_name,
            "Contact Person2 Email": contact2_email,
            "Contact Person2 Name": contact2_name,
            "RDV Date": start_date + timedelta(days=current_day - 1),
            "Start Time": start_time.strftime("%H:%M"),
            "End Time": end_time.strftime("%H:%M"),
            "Duration": duration,
            "Location": location,
            "Manager1 Email": manager1_email,
            "Manager1 Name": manager1_name,
            "Manager2 Email": manager2_email or "None",
            "Manager2 Name": manager2_name or "None",
            "Status": "Planned",
            "Hired Date": start_date.strftime("%Y-%m-%d")
        })

        current_datetime = end_time

        if current_datetime.time() >= datetime.strptime("18:00", "%H:%M").time():
            current_day += 1
            current_datetime = datetime.combine(start_date + timedelta(days=current_day - 1), datetime.strptime("09:00", "%H:%M").time())

    return pd.DataFrame(schedule)
