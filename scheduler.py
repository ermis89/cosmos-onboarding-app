import pandas as pd
from datetime import timedelta

def generate_schedule(template_df, role_sheet, start_date, name, email,
                      mgr1_name, mgr1_email, mgr2_name, mgr2_email):
    df = template_df.copy()
    df = df[df["Role Group"].notna()].reset_index(drop=True)
    df["Order"] = df.index + 1

    schedule = []
    day_cursor = start_date
    current_time = None
    daily_end = None

    def get_daily_start_end(day_num):
        if day_num == 1:
            return pd.to_datetime("10:00", format="%H:%M"), pd.to_datetime("18:00", format="%H:%M")
        else:
            return pd.to_datetime("09:00", format="%H:%M"), pd.to_datetime("17:00", format="%H:%M")

    day_num = 1
    current_time, daily_end = get_daily_start_end(day_num)

    for _, row in df.iterrows():
        duration = timedelta(minutes=int(row["Duration"]))
        if current_time + duration > daily_end:
            day_num += 1
            day_cursor = start_date + timedelta(days=day_num - 1)
            current_time, daily_end = get_daily_start_end(day_num)

        start_str = current_time.strftime("%H:%M")
        end_time = current_time + duration
        end_str = end_time.strftime("%H:%M")

        schedule.append({
            "Newcomer Email": email,
            "Newcomer Name": name,
            "Role": row["Role Group"],
            "RDV": row["RDV Title"],
            "Short RDV Description": row["RDV Description"],
            "Contact Person1 Email": row.get("Contact Person", "None"),
            "Contact Person1 Name": row.get("Contact Person Name", "None"),
            "Contact Person2 Email": row.get("Contact Person 2", "None"),
            "Contact Person2 Name": row.get("Contact Person 2 Name", "None"),
            "RDV Date": day_cursor.strftime("%Y-%m-%d"),
            "Start Time": start_str,
            "End Time": end_str,
            "Duration": int(row["Duration"]),
            "Location": row.get("Location", "None"),
            "Manager1 Email": mgr1_email,
            "Manager1 Name": mgr1_name,
            "Manager2 Email": mgr2_email or "None",
            "Manager2 Name": mgr2_name or "None",
            "Status": "Planned",
            "Hired Date": start_date.strftime("%Y-%m-%d")
        })

        current_time = end_time

    return pd.DataFrame(schedule)
