import pandas as pd
from datetime import datetime, timedelta, time

# ────────────────────────────────────────────────────────────────
#  Day template
# ────────────────────────────────────────────────────────────────
def day_bounds(day_idx: int):
    """Return (start, end, breaks) tuple for the given 0‑based day index."""
    if day_idx == 0:                                   # Day‑1
        start, end = time(10, 0), time(18, 0)
        breaks = [
            (time(11, 30), time(12, 0)),
            (time(13, 30), time(14, 30)),              # shifted lunch
            (time(15, 30), time(16, 0)),
        ]
    else:                                              # Day‑2+
        start, end = time(9, 0), time(17, 0)
        breaks = [
            (time(10, 30), time(11, 0)),
            (time(13, 0),  time(14, 0)),
            (time(15, 30), time(16, 0)),
        ]
    return start, end, breaks


# ────────────────────────────────────────────────────────────────
#  Auto‑generate schedule (NO splitting across blocks)
# ────────────────────────────────────────────────────────────────
def generate_schedule(df_template: pd.DataFrame,
                      role: str,
                      hire_date,                         # date or datetime
                      newcom_name: str, newcom_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str = "", mgr2_email: str = "") -> pd.DataFrame:

    if isinstance(hire_date, datetime):
        hire_date = hire_date.date()

    rdvs = (df_template[df_template["Role"].str.strip() == role.strip()]
            .sort_values("Order")
            .reset_index(drop=True))

    if rdvs.empty():
        raise ValueError(f"No rows found for role “{role}”. Check the spreadsheet.")

    rows, day_idx, rdv_idx = [], 0, 0
    while rdv_idx < len(rdvs):

        # skip weekends
        day_date = hire_date + timedelta(days=day_idx)
        while day_date.weekday() >= 5:                  # Sat/Sun
            day_idx += 1
            day_date = hire_date + timedelta(days=day_idx)

        # build working blocks for that day
        day_start, day_end, breaks = day_bounds(day_idx)
        blocks, ptr = [], datetime.combine(day_date, day_start)
        for bs, be in breaks + [(day_end, day_end)]:
            blocks.append((ptr, datetime.combine(day_date, bs)))
            ptr = datetime.combine(day_date, be)

        # place RDVs
        for bl_s, bl_e in blocks:
            cursor = max(ptr, bl_s)
            while rdv_idx < len(rdvs):
                rdv = rdvs.loc[rdv_idx]
                dur = int(rdv["Duration"])
                rdv_end = cursor + timedelta(minutes=dur)

                if rdv_end <= bl_e:
                    rows.append(make_row(
                        rdv, newcom_name, newcom_email,
                        mgr1_name, mgr1_email,
                        mgr2_name, mgr2_email,
                        cursor, rdv_end, day_date
                    ))
                    cursor = rdv_end
                    rdv_idx += 1
                else:
                    break  # RDV moves to next block/day
        day_idx += 1

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


# ────────────────────────────────────────────────────────────────
#  Merge manager‑priority RDVs
# ────────────────────────────────────────────────────────────────
def merge_manual_rdvs(auto_df: pd.DataFrame,
                      manual_df: pd.DataFrame,
                      newcom_name: str, newcom_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str, mgr2_email: str) -> pd.DataFrame:
    """Insert manual RDVs; reschedule (do not delete) collided auto RDVs."""
    def to_dt(d, t):
        return datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")

    manual_rows, occupied = [], []
    for _, r in manual_df.iterrows():
        s_dt = to_dt(r["Date"].strftime("%Y-%m-%d"), r["Start"])
        e_dt = to_dt(r["Date"].strftime("%Y-%m-%d"), r["End"])
        manual_rows.append({
            "Newcomer Email": newcom_email,
            "Newcomer Name":  newcom_name,
            "Role Group":     auto_df["Role Group"].iloc[0] if not auto_df.empty else "",
            "RDV Title":      r["Title"],
            "RDV Description": r["Description"],
            "Contact Person1 Email": r["C1 Email"],
            "Contact Person1 Name":  r["C1 Name"],
            "Contact Person2 Email": r["C2 Email"],
            "Contact Person2 Name":  r["C2 Name"],
            "RDV Date":  s_dt.date().isoformat(),
            "Start Time": s_dt.strftime("%H:%M"),
            "End Time":   e_dt.strftime("%H:%M"),
            "Duration":   int((e_dt - s_dt).seconds // 60),
            "Location":   r.get("Location", ""),
            "Manager1 Email": mgr1_email,
            "Manager1 Name":  mgr1_name,
            "Manager2 Email": mgr2_email,
            "Manager2 Name":  mgr2_name,
            "Status": "Planned (manual)",
            "Hired Date": s_dt.date().isoformat()
        })
        occupied.append((s_dt, e_dt))

    manual_df_clean = pd.DataFrame(manual_rows)

    # split auto into keep & queue
    queue, keep = [], []
    for _, a in auto_df.iterrows():
        a_s = to_dt(a["RDV Date"], a["Start Time"])
        a_e = to_dt(a["RDV Date"], a["End Time"])
        if any(not (a_e <= o_s or a_s >= o_e) for o_s, o_e in occupied):
            queue.append(a)
        else:
            keep.append(a)

    # reschedule queued RDVs
    if queue:
        keep.extend(_reschedule_queue(pd.DataFrame(queue), occupied))

    final = pd.concat([manual_df_clean, pd.DataFrame(keep)], ignore_index=True)
    return final.sort_values(["RDV Date", "Start Time"]).reset_index(drop=True)


# ────────────────────────────────────────────────────────────────
#  Reschedule queued RDVs helper
# ────────────────────────────────────────────────────────────────
def _reschedule_queue(queue_df: pd.DataFrame, occupied):
    """Reschedule queued RDVs respecting breaks & weekends."""
    moved = []

    def next_workday(dt):
        nxt = dt.date() + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        return datetime.combine(nxt, time(9, 0))

    for _, rdv in queue_df.sort_values(["RDV Date", "Start Time"]).iterrows():
        dur = int(rdv["Duration"])
        cur = datetime.strptime(f"{rdv['RDV Date']} {rdv['Start Time']}", "%Y-%m-%d %H:%M")
        placed = False
        while not placed:
            idx = (cur.date() - occupied[0][0].date()).days
            d_start, d_end, breaks = day_bounds(idx)

            # drop breaks fully covered by occupied intervals
            breaks = [
                (bs, be) for (bs, be) in breaks
                if not any(o.date() == cur.date() and o.time() <= bs and be <= e.time()
                           for o, e in occupied)
            ]

            blocks, ptr = [], datetime.combine(cur.date(), d_start)
            for bs, be in breaks + [(d_end, d_end)]:
                blocks.append((ptr, datetime.combine(cur.date(), bs)))
                ptr = datetime.combine(cur.date(), be)

            for bl_s, bl_e in blocks:
                if bl_e <= cur:
                    continue
                start, end = max(bl_s, cur), None
                end = start + timedelta(minutes=dur)
                if end > bl_e:
                    continue
                clash = any(not (end <= o_s or start >= o_e) for o_s, o_e in occupied)
                if not clash:
                    n = rdv.copy()
                    n["RDV Date"] = start.date().isoformat()
                    n["Start Time"] = start.strftime("%H:%M")
                    n["End Time"]   = end.strftime("%H:%M")
                    occupied.append((start, end))
                    moved.append(n)
                    placed = True
                    break
            if not placed:
                cur = next_workday(cur)
    return moved


# ────────────────────────────────────────────────────────────────
#  Helper to build row dict
# ────────────────────────────────────────────────────────────────
def make_row(rdv, new_name, new_email,
             m1_name, m1_email, m2_name, m2_email,
             start_dt, end_dt, day_date):
    return {
        "Newcomer Email": new_email,
        "Newcomer Name":  new_name,
        "Role Group":     rdv["Role"],
        "RDV Title":      rdv["RDV"],
        "RDV Description": rdv["Short RDV Description"],
        "Contact Person1 Email": rdv.get("Contact Person1 Email", ""),
        "Contact Person1 Name":  rdv.get("Contact Person1 Name", ""),
        "Contact Person2 Email": rdv.get("Contact Person2 Email", ""),
        "Contact Person2 Name":  rdv.get("Contact Person2 Name", ""),
        "
