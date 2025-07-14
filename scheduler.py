import pandas as pd
from datetime import datetime, timedelta

# ──────────────────────────── Helper
def to_time(hm: str):
    return datetime.strptime(hm, "%H:%M")

# ──────────────────────────── Break tables
BREAKS_DAY1   = [(to_time("11:30"), to_time("12:00")),
                 (to_time("13:00"), to_time("14:00")),
                 (to_time("15:30"), to_time("16:00"))]

BREAKS_OTHER  = [(to_time("10:30"), to_time("11:00")),
                 (to_time("13:00"), to_time("14:00")),
                 (to_time("15:30"), to_time("16:00"))]

def day_config(day_index: int):
    if day_index == 0:
        return to_time("10:00"), to_time("18:00"), BREAKS_DAY1
    return to_time("09:00"), to_time("17:00"), BREAKS_OTHER

# ──────────────────────────── Main scheduler
def generate_schedule(
        template_df, role, hire_date,
        new_name, new_email,
        mgr1_name, mgr1_email,
        mgr2_name="", mgr2_email=""):

    rdvs = template_df[template_df["Role"] == role].reset_index(drop=True)
    if rdvs.empty:
        return pd.DataFrame()  # nothing for that role

    schedule = []
    day_idx    = 0
    rdv_cursor = 0

    while rdv_cursor < len(rdvs):
        work_start, work_end, breaks = day_config(day_idx)
        current_dt = datetime.combine(hire_date + timedelta(days=day_idx),
                                      work_start.time())

        # iterate day slots (work blocks separated by breaks)
        for brk_start, brk_end in breaks + [(work_end, work_end)]:
            while rdv_cursor < len(rdvs):
                rdv = rdvs.loc[rdv_cursor]
                duration = int(rdv["Duration"])
                rdv_end_dt = current_dt + timedelta(minutes=duration)

                # if RDV fits before next break
                if rdv_end_dt.time() <= brk_start.time():
                    schedule.append({
                        "Newcomer Email": new_email,
                        "Newcomer Name":  new_name,
                        "Role":           role,
                        "RDV":            rdv["RDV"],
                        "Short RDV Description": rdv["Short RDV Description"],
                        "Contact Person1 Email": rdv.get("Contact Person1 Email", ""),
                        "Contact Person1 Name":  rdv.get("Contact Person1 Name", ""),
                        "Contact Person2 Email": rdv.get("Contact Person2 Email", ""),
                        "Contact Person2 Name":  rdv.get("Contact Person2 Name", ""),
                        "RDV Date":  current_dt.date().isoformat(),
                        "Start Time": current_dt.time().strftime("%H:%M"),
                        "End Time":   rdv_end_dt.time().strftime("%H:%M"),
                        "Duration":   duration,
                        "Location":   rdv.get("Location", ""),
                        "Manager1 Email": mgr1_email,
                        "Manager1 Name":  mgr1_name,
                        "Manager2 Email": mgr2_email or "",
                        "Manager2 Name":  mgr2_name or "",
                        "Status":     "Planned",
                        "Hired Date": hire_date.isoformat()
                    })
                    current_dt = rdv_end_dt
                    rdv_cursor += 1
                else:
                    break  # next break / end-of-day
            # jump over break
            if current_dt.time() < brk_start.time():
                current_dt = current_dt.replace(
                    hour=brk_end.hour, minute=brk_end.minute)
        day_idx += 1  # next day loop

    return pd.DataFrame(schedule)
