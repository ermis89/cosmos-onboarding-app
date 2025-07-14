from datetime import datetime, timedelta, time
import pandas as pd

# ------------------------------------------------------------
# helper functions
def t(hhmm: str) -> time:
    """Return a time object from 'HH:MM' string."""
    return datetime.strptime(hhmm, "%H:%M").time()

def add_minutes(base: time, minutes: int) -> time:
    dt = datetime.combine(datetime.today(), base) + timedelta(minutes=minutes)
    return dt.time()
# ------------------------------------------------------------

def _day_config(day_index: int):
    """Return work start, work end, break list for given day number (0 = first day)."""
    if day_index == 0:
        work_start, work_end = t("10:00"), t("18:00")
        breaks = [(t("11:30"), t("12:00")),
                  (t("13:00"), t("14:00")),
                  (t("15:30"), t("16:00"))]
    else:
        work_start, work_end = t("09:00"), t("17:00")
        breaks = [(t("10:30"), t("11:00")),
                  (t("13:00"), t("14:00")),
                  (t("15:30"), t("16:00"))]
    return work_start, work_end, breaks

# ------------------------------------------------------------
def generate_schedule(df_template: pd.DataFrame,
                      role: str,
                      hire_date,
                      newcomer_name, newcomer_email,
                      mgr1_name, mgr1_email,
                      mgr2_name="", mgr2_email=""):
    """
    Build a multi-day onboarding schedule.
    hire_date is a python date object (comes from st.date_input)
    """
    rdvs = df_template[df_template["Role"] == role].reset_index(drop=True)

    schedule = []
    day_offset = 0
    rdv_idx = 0

    while rdv_idx < len(rdvs):
        work_start, work_end, breaks = _day_config(day_offset)
        day_date = hire_date + timedelta(days=day_offset)
        current = work_start

        # iterate through blocks of the day
        for brk_start, brk_end in breaks + [(work_end, work_end)]:
            while rdv_idx < len(rdvs):
                rdv = rdvs.iloc[rdv_idx]
                dur = int(rdv["Duration"])
                # if RDV fits before next break/end
                end_candidate = add_minutes(current, dur)
                if end_candidate <= brk_start:
                    # append row
                    schedule.append({
                        "Newcomer Email": newcomer_email,
                        "Newcomer Name": newcomer_name,
                        "Role Group": role,
                        "RDV Title": rdv["RDV"],
                        "RDV Description": rdv["Short RDV Description"],
                        "Contact Person1 Email": rdv.get("Contact Person1 Email", ""),
                        "Contact Person1 Name":  rdv.get("Contact Person1 Name", ""),
                        "Contact Person2 Email": rdv.get("Contact Person2 Email", ""),
                        "Contact Person2 Name":  rdv.get("Contact Person2 Name", ""),
                        "RDV Date": day_date.strftime("%Y-%m-%d"),
                        "Start Time": current.strftime("%H:%M"),
                        "End Time":   end_candidate.strftime("%H:%M"),
                        "Duration": dur,
                        "Location": rdv["Location"],
                        "Manager1 Email": mgr1_email,
                        "Manager1 Name":  mgr1_name,
                        "Manager2 Email": mgr2_email,
                        "Manager2 Name":  mgr2_name,
                        "Status": "Planned",
                        "Hired Date": hire_date.strftime("%Y-%m-%d")
                    })
                    current = end_candidate
                    rdv_idx += 1
                else:
                    break  # doesn’t fit, go to break or next day
            # jump over the break
            if current < brk_start:
                current = brk_end
        day_offset += 1  # move to next calendar day

    return pd.DataFrame(schedule)
