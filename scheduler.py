import pandas as pd
from datetime import datetime, timedelta

# ── helper to build daily config ───────────────────────────────────
def day_bounds(day_idx: int):
    if day_idx == 0:                               # Day 1
        start = datetime.strptime("10:00", "%H:%M")
        end   = datetime.strptime("18:00", "%H:%M")
        breaks = [
            (datetime.strptime("11:30", "%H:%M"), datetime.strptime("12:00", "%H:%M")),
            (datetime.strptime("13:00", "%H:%M"), datetime.strptime("14:00", "%H:%M")),
            (datetime.strptime("15:30", "%H:%M"), datetime.strptime("16:00", "%H:%M")),
        ]
    else:                                          # Other days
        start = datetime.strptime("09:00", "%H:%M")
        end   = datetime.strptime("17:00", "%H:%M")
        breaks = [
            (datetime.strptime("10:30", "%H:%M"), datetime.strptime("11:00", "%H:%M")),
            (datetime.strptime("13:00", "%H:%M"), datetime.strptime("14:00", "%H:%M")),
            (datetime.strptime("15:30", "%H:%M"), datetime.strptime("16:00", "%H:%M")),
        ]
    return start, end, breaks

# ── main generator ────────────────────────────────────────────────
def generate_schedule(df, role, hire_date,
                      newcom_name, newcom_email,
                      mgr1_name, mgr1_email,
                      mgr2_name="", mgr2_email="") -> pd.DataFrame:

    # Ensure hire_date is full datetime
    hire_date = datetime.combine(hire_date, datetime.min.time())

    rdvs = df[df["Role"] == role].reset_index(drop=True)
    if rdvs.empty:
        return pd.DataFrame()

    out = []
    day_idx = 0
    rdv_cursor = 0

    while rdv_cursor < len(rdvs):
        day_start_t, day_end_t, breaks = day_bounds(day_idx)
        day_date = hire_date + timedelta(days=day_idx)
        current_dt = datetime.combine(day_date, day_start_t.time())

        for brk_start_t, brk_end_t in breaks + [(day_end_t, day_end_t)]:
            brk_start = datetime.combine(day_date, brk_start_t.time())
            brk_end   = datetime.combine(day_date, brk_end_t.time())

            while rdv_cursor < len(rdvs):
                rdv = rdvs.loc[rdv_cursor]
                dur = int(rdv["Duration"])
                rdv_end = current_dt + timedelta(minutes=dur)

                if rdv_end <= brk_start:
                    out.append(make_row(rdv, newcom_name, newcom_email,
                                        mgr1_name, mgr1_email,
                                        mgr2_name, mgr2_email,
                                        current_dt, rdv_end, day_date))
                    current_dt = rdv_end
                    rdv_cursor += 1
                else:
                    break

            if brk_end_t != day_end_t:
                out.append(make_break_row(brk_start, brk_end, day_date,
                           "Break (Lunch)" if (brk_end - brk_start).seconds >= 3500
                           else "Break (Short)",
                           newcom_email, newcom_name))
                current_dt = brk_end

        day_idx += 1

    return pd.DataFrame(out)

# ── helpers to build row dicts ────────────────────────────────────
def make_row(r, new_name, new_email,
             m1_name, m1_email, m2_name, m2_email,
             start_dt, end_dt, day_date):
    return {
        "Newcomer Email": new_email,
        "Newcomer Name":  new_name,
        "Role": r["Role"],
        "RDV":  r["RDV"],
        "Short RDV Description": r["Short RDV Description"],
        "Contact Person1 Email": r.get("Contact Person1 Email", ""),
        "Contact Person1 Name":  r.get("Contact Person1 Name", ""),
        "Contact Person2 Email": r.get("Contact Person2 Email", ""),
        "Contact Person2 Name":  r.get("Contact Person2 Name", ""),
        "RDV Date":  day_date.isoformat(),
        "Start Time": start_dt.strftime("%H:%M"),
        "End Time":   end_dt.strftime("%H:%M"),
        "Duration":   int(r["Duration"]),
        "Location":   r.get("Location", ""),
        "Manager1 Email": m1_email,
        "Manager1 Name":  m1_name,
        "Manager2 Email": m2_email,
        "Manager2 Name":  m2_name,
        "Status": "Planned",
        "Hired Date": day_date.isoformat()
    }

def make_break_row(start_dt, end_dt, day_date, title, new_email, new_name):
    return {
        "Newcomer Email": new_email,
        "Newcomer Name":  new_name,
        "Role": "",
        "RDV":  title,
        "Short RDV Description": title,
        "Contact Person1 Email": "",
        "Contact Person1 Name":  "",
        "Contact Person2 Email": "",
        "Contact Person2 Name":  "",
        "RDV Date":  day_date.isoformat(),
        "Start Time": start_dt.strftime("%H:%M"),
        "End Time":   end_dt.strftime("%H:%M"),
        "Duration":   int((end_dt - start_dt).seconds // 60),
        "Location":   "",
        "Manager1 Email": "",
        "Manager1 Name":  "",
        "Manager2 Email": "",
        "Manager2 Name":  "",
        "Status": "Planned",
        "Hired Date": day_date.isoformat()
    }
