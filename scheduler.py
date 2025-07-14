
import pandas as pd
from datetime import datetime, timedelta

def generate_schedule(df, role, start_date, newcomer_name, newcomer_email, m1_name, m1_email, m2_name, m2_email):
    df = df.copy()
    df = df[df["Role"] == role]

    day_limit_minutes = 6 * 60
    first_day_start = datetime.combine(start_date, datetime.strptime("10:00", "%H:%M").time())
    normal_day_start_time = "09:00"

    output = []
    current_day = start_date
    current_time = first_day_start
    day_minutes = 0
    day_count = 1

    for idx, row in df.iterrows():
        duration = int(row["Duration"])
        location = str(row["Location"]).strip()

        if day_minutes + duration > day_limit_minutes:
            day_count += 1
            current_day = start_date + timedelta(days=day_count - 1)
            start_time_str = normal_day_start_time if day_count > 1 else "10:00"
            current_time = datetime.combine(current_day, datetime.strptime(start_time_str, "%H:%M").time())
            day_minutes = 0

        if day_minutes == 90:
            output.append(create_break(current_day, current_time, 30, "Break1"))
            current_time += timedelta(minutes=30)
            day_minutes += 30
        elif day_minutes == 240:
            output.append(create_break(current_day, current_time, 60, "Break2"))
            current_time += timedelta(minutes=60)
            day_minutes += 60

        end_time = current_time + timedelta(minutes=duration)
        output.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name": newcomer_name,
            "Role Group": row["Role"],
            "RDV Title": row["RDV"],
            "RDV Description": row["Short RDV Description"],
            "Contact Person1 Email": row.get("Contact Person1 Email", "None"),
            "Contact Person1 Name": row.get("Contact Person1 Name", "None"),
            "Contact Person2 Email": row.get("Contact Person2 Email", "None"),
            "Contact Person2 Name": row.get("Contact Person2 Name", "None"),
            "RDV Date": current_day.strftime("%Y-%m-%d"),
            "Start Time": current_time.strftime("%H:%M"),
            "End Time": end_time.strftime("%H:%M"),
            "Duration": duration,
            "Location": location,
            "Manager1 Email": m1_email,
            "Manager1 Name": m1_name,
            "Manager2 Email": m2_email or "None",
            "Manager2 Name": m2_name or "None",
            "Status": "Planned",
            "Hired Date": start_date.strftime("%Y-%m-%d")
        })
        current_time = end_time
        day_minutes += duration

    return pd.DataFrame(output)

def create_break(day, start_time, duration, title):
    end_time = start_time + timedelta(minutes=duration)
    return {
        "Newcomer Email": "Break",
        "Newcomer Name": "Break",
        "Role Group": "",
        "RDV Title": title,
        "RDV Description": "Short Break" if duration == 30 else "Long Break",
        "Contact Person1 Email": "None",
        "Contact Person1 Name": "None",
        "Contact Person2 Email": "None",
        "Contact Person2 Name": "None",
        "RDV Date": day.strftime("%Y-%m-%d"),
        "Start Time": start_time.strftime("%H:%M"),
        "End Time": end_time.strftime("%H:%M"),
        "Duration": duration,
        "Location": "",
        "Manager1 Email": "None",
        "Manager1 Name": "None",
        "Manager2 Email": "None",
        "Manager2 Name": "None",
        "Status": "Planned",
        "Hired Date": day.strftime("%Y-%m-%d")
    }
