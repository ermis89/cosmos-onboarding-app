
from datetime import datetime, timedelta, time
import pandas as pd

def parse_time(t):
    if pd.isna(t): return None
    if isinstance(t, str): return datetime.strptime(t.strip(), "%H:%M").time()
    return t if isinstance(t, time) else datetime.strptime(str(t), "%H:%M:%S").time()

def add_minutes(base_time, minutes):
    dt = datetime.combine(datetime.today(), base_time) + timedelta(minutes=minutes)
    return dt.time()

def generate_schedule(start_date, rdvs, newcomer_name, newcomer_email, m1_name, m1_email, m2_name, m2_email):
    schedule = []
    current_day = start_date
    work_start = time(9, 0)
    work_end = time(17, 0)
    breaks = [(time(11,30), time(12,0)), (time(13,30), time(14,30))]

    current_time = work_start
    for rdv in rdvs:
        duration = int(rdv.get("Duration", 60))
        location = rdv.get("Location", "")
        contact_name1 = rdv.get("Contact Person 1", "")
        contact_email1 = rdv.get("Contact Email 1", "")
        contact_name2 = rdv.get("Contact Person 2", "")
        contact_email2 = rdv.get("Contact Email 2", "")

        # Adjust working time if Cosmos Academy
        if location.lower() == "cosmos academy":
            work_start = time(15, 0)
            work_end = time(17, 0)

        # Reset to next day if overflow
        while True:
            available = (datetime.combine(datetime.today(), work_end) - datetime.combine(datetime.today(), current_time)).seconds // 60
            if available >= duration:
                break
            current_day += timedelta(days=1)
            current_time = time(9, 0)
            work_start = time(9, 0)
            work_end = time(17, 0)

        end_time = add_minutes(current_time, duration)
        schedule.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name": newcomer_name,
            "Role Group": rdv.get("Role", ""),
            "RDV Title": rdv.get("RDV", ""),
            "RDV Description": rdv.get("Short RDV Description", ""),
            "Contact Person1 Email": contact_email1 if contact_email1 else "None",
            "Contact Person1 Name": contact_name1 if contact_name1 else "None",
            "Contact Person2 Email": contact_email2 if contact_email2 else "None",
            "Contact Person2 Name": contact_name2 if contact_name2 else "None",
            "RDV Date": current_day.strftime("%Y-%m-%d"),
            "Start Time": current_time.strftime("%H:%M"),
            "End Time": end_time.strftime("%H:%M"),
            "Duration": duration,
            "Location": location,
            "Manager1 Email": m1_email,
            "Manager1 Name": m1_name,
            "Manager2 Email": m2_email if m2_email else "None",
            "Manager2 Name": m2_name if m2_name else "None",
            "Status": "Planned",
            "Hired Date": start_date.strftime("%Y-%m-%d")
        })
        current_time = end_time

    return pd.DataFrame(schedule)
