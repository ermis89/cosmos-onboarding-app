import pandas as pd
from datetime import datetime, timedelta, time

# ────────────────────────────────────────────────────────────────
#  Day template
# ────────────────────────────────────────────────────────────────
def day_bounds(day_idx: int):
    """Return work‑day start, end, and break windows for a 0‑based day index."""
    if day_idx == 0:  # first day
        start = time(10, 0)
        end   = time(18, 0)
        breaks = [
            (time(11, 30), time(12,  0)),
            (time(13, 30), time(14, 30)),   # shifted lunch
            (time(15, 30), time(16,  0)),
        ]
    else:             # day‑2+
        start = time( 9, 0)
        end   = time(17, 0)
        breaks = [
            (time(10, 30), time(11,  0)),
            (time(13,  0), time(14,  0)),
            (time(15, 30), time(16,  0)),
        ]
    return start, end, breaks


# ────────────────────────────────────────────────────────────────
#  Main auto scheduler  (no splitting)
# ────────────────────────────────────────────────────────────────
def generate_schedule(df_template: pd.DataFrame,
                      role: str,
                      hire_date,
                      newcomer_name: str,
                      newcomer_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str = "", mgr2_email: str = "") -> pd.DataFrame:

    if isinstance(hire_date, datetime):
        hire_date = hire_date.date()

    rdvs = (df_template[df_template["Role"].str.strip() == role.strip()]
            .sort_values("Order")
            .reset_index(drop=True))
    if rdvs.empty:
        return pd.DataFrame(columns=OUTPUT_COLS)

    rows, day_idx, rdv_idx = [], 0, 0
    while rdv_idx < len(rdvs):

        # skip weekends
        day_date = hire_date + timedelta(days=day_idx)
        while day_date.weekday() >= 5:
            day_idx += 1
            day_date = hire_date + timedelta(days=day_idx)

        # build day blocks
        day_start, day_end, breaks = day_bounds(day_idx)
        blocks, cursor = [], datetime.combine(day_date, day_start)
        for bs, be in breaks + [(day_end, day_end)]:
            blocks.append((cursor, datetime.combine(day_date, bs)))
            cursor = datetime.combine(day_date, be)

        # fill blocks
        for bl_start, bl_end in blocks:
            cursor_dt = max(cursor, bl_start)
            while rdv_idx < len(rdvs):
                rdv      = rdvs.loc[rdv_idx]
                dur_min  = int(rdv["Duration"])
                rdv_end  = cursor_dt + timedelta(minutes=dur_min)

                if rdv_end <= bl_end:  # fits entirely
                    rows.append(make_row(
                        rdv, newcomer_name, newcomer_email,
                        mgr1_name, mgr1_email, mgr2_name, mgr2_email,
                        cursor_dt, rdv_end, day_date
                    ))
                    cursor_dt = rdv_end
                    rdv_idx  += 1
                else:
                    break  # whole RDV moves to next block/day
        day_idx += 1

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


# ────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────
OUTPUT_COLS = [
    "Newcomer Email", "Newcomer Name", "Role Group",
    "RDV Title", "RDV Description",
    "Contact Person1 Email", "Contact Person1 Name",
    "Contact Person2 Email", "Contact Person2 Name",
    "RDV Date", "Start Time", "End Time", "Duration",
    "Location", "Manager1 Email", "Manager1 Name",
    "Manager2 Email", "Manager2 Name",
    "Status", "Hired Date"
]

def make_row(rdv, newcomer_name, newcomer_email,
             mgr1_name, mgr1_email, mgr2_name, mgr2_email,
             start_dt, end_dt, day_date):
    return {
        "Newcomer Email": newcomer_email,
        "Newcomer Name":  newcomer_name,
        "Role Group":     rdv["Role"],
        "RDV Title":      rdv["RDV"],
        "RDV Description": rdv["Short RDV Description"],
        "Contact Person1 Email": rdv.get("Contact Person1 Email", ""),
        "Contact Person1 Name":  rdv.get("Contact Person1 Name", ""),
        "Contact Person2 Email": rdv.get("Contact Person2 Email", ""),
        "Contact Person2 Name":  rdv.get("Contact Person2 Name", ""),
        "RDV Date":  day_date.isoformat(),
        "Start Time": start_dt.strftime("%H:%M"),
        "End Time":   end_dt.strftime("%H:%M"),
        "Duration":   int(rdv["Duration"]),
        "Location":   rdv.get("Location", ""),
        "Manager1 Email": mgr1_email,
        "Manager1 Name":  mgr1_name,
        "Manager2 Email": mgr2_email,
        "Manager2 Name":  mgr2_name,
        "Status": "Planned",
        "Hired Date": day_date.isoformat()
    }


# ────────────────────────────────────────────────────────────────
#  Merge manual RDVs  (priority overrides)
# ────────────────────────────────────────────────────────────────
def merge_manual_rdvs(auto_df, manual_df,
                      newcomer_name, newcomer_email,
                      mgr1_name, mgr1_email,
                      mgr2_name, mgr2_email):

    def to_dt(d, t):
        return datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")

    # manual rows → 20‑col
    manual_rows = []
    for _, row in manual_df.iterrows():
        s_dt = to_dt(row["Date"].strftime("%Y-%m-%d"), row["Start"])
        e_dt = to_dt(row["Date"].strftime("%Y-%m-%d"), row["End"])
        manual_rows.append({
            "Newcomer Email": newcomer_email,
            "Newcomer Name":  newcomer_name,
            "Role Group":     auto_df["Role Group"].iloc[0] if not auto_df.empty else "",
            "RDV Title":      row["Title"],
            "RDV Description": row["Description"],
            "Contact Person1 Email": row["C1 Email"],
            "Contact Person1 Name":  row["C1 Name"],
            "Contact Person2 Email": row["C2 Email"],
            "Contact Person2 Name":  row["C2 Name"],
            "RDV Date":  s_dt.date().isoformat(),
            "Start Time": s_dt.strftime("%H:%M"),
            "End Time":   e_dt.strftime("%H:%M"),
            "Duration":   int((e_dt - s_dt).seconds // 60),
            "Location":   row.get("Location", ""),
            "Manager1 Email": mgr1_email,
            "Manager1 Name":  mgr1_name,
            "Manager2 Email": mgr2_email,
            "Manager2 Name":  mgr2_name,
            "Status": "Planned (manual)",
            "Hired Date": s_dt.date().isoformat()
        })

    manual_df_clean = pd.DataFrame(manual_rows)

    # build occupied list
    occ = [(to_dt(r["RDV Date"], r["Start Time"]),
            to_dt(r["RDV Date"], r["End Time"])) for _, r in manual_df_clean.iterrows()]

    # split auto into keep/queue
    queue, keep = [], []
    for _, a in auto_df.iterrows():
        a_s, a_e = to_dt(a["RDV Date"], a["Start Time"]), to_dt(a["RDV Date"], a["End Time"])
        if any(not (a_e <= o_s or a_s >= o_e) for o_s, o_e in occ):
            queue.append(a)
        else:
            keep.append(a)

    if queue:
        moved = _reschedule_queue(pd.DataFrame(queue), occ)
        keep.extend(moved)

    final_df = pd.concat([manual_df_clean, pd.DataFrame(keep)], ignore_index=True)
    final_df = final_df.sort_values(["RDV Date", "Start Time"]).reset_index(drop=True)
    return final_df


# ────────────────────────────────────────────────────────────────
#  Mini‑scheduler for queued RDVs
# ────────────────────────────────────────────────────────────────
def _reschedule_queue(queue_df, occupied):
    moved = []

    def next_day_start(d):  # 09:00 next work‑day
        nxt = d + timedelta(days=1)
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

            # drop breaks swallowed by occupied intervals
            breaks = [
                (bs, be) for (bs, be) in breaks
                if not any(o.date() == cur.date() and o.time() <= bs and be <= e.time()
                           for o, e in occupied)
            ]

            # build free blocks
            blocks, ptr = [], datetime.combine(cur.date(), d_start)
            for bs, be in breaks + [(d_end, d_end)]:
                blocks.append((ptr, datetime.combine(cur.date(), bs)))
                ptr = datetime.combine(cur.date(), be)

            for bl_s, bl_e in blocks:
                if bl_e <= cur:
                    continue
                start = max(bl_s, cur)
                end   = start + timedelta(minutes=dur)
                if end > bl_e:
                    continue
                clash = any(not (end <= o_s or start >= o_e) for o_s, o_e in occupied)
                if not clash:
                    new_r = rdv.copy()
                    new_r["RDV Date"]   = start.date().isoformat()
                    new_r["Start Time"] = start.strftime("%H:%M")
                    new_r["End Time"]   = end.strftime("%H:%M")
                    occupied.append((start, end))
                    moved.append(new_r)
                    placed = True
                    break
            if not placed:
                cur = next_day_start(cur.date())
    return moved
