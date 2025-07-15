import pandas as pd
from datetime import datetime, timedelta, time

# ── day template ────────────────────────────────────────────────
def day_bounds(day_idx: int):
    """Return work‑day start, end, and break windows for a 0‑based day index."""
    if day_idx == 0:                                   # Day‑1 template
        start = time(10, 0)
        end   = time(18, 0)
        breaks = [
            (time(11, 30), time(12,  0)),   # coffee
            (time(13, 30), time(14, 30)),   # lunch (shifted)
            (time(15, 30), time(16,  0)),   # coffee
        ]
    else:                                              # Day‑2+
        start = time( 9, 0)
        end   = time(17, 0)
        breaks = [
            (time(10, 30), time(11,  0)),
            (time(13,  0), time(14,  0)),
            (time(15, 30), time(16,  0)),
        ]
    return start, end, breaks


# ── public API ──────────────────────────────────────────────────
def generate_schedule(df_template: pd.DataFrame,
                      role: str,
                      hire_date,                # datetime.date | datetime
                      newcomer_name: str,
                      newcomer_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str = "", mgr2_email: str = "") -> pd.DataFrame:
    """
    Build auto schedule for the given role & hire date.
    Returns a DataFrame with the 20 required columns.
    """
    if isinstance(hire_date, datetime):
        hire_date = hire_date.date()

    rdvs = (df_template[df_template["Role"].str.strip() == role.strip()]
            .sort_values("Order")
            .reset_index(drop=True))

    if rdvs.empty:
        return pd.DataFrame()

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
            cursor_dt = bl_start
            while rdv_idx < len(rdvs):
                rdv      = rdvs.loc[rdv_idx]
                dur_min  = int(rdv["Duration"])
                rdv_end  = cursor_dt + timedelta(minutes=dur_min)

                if rdv_end <= bl_end:
                    rows.append(make_row(
                        rdv, newcomer_name, newcomer_email,
                        mgr1_name, mgr1_email, mgr2_name, mgr2_email,
                        cursor_dt, rdv_end, day_date
                    ))
                    cursor_dt = rdv_end
                    rdv_idx  += 1
                else:
                    remaining = int((bl_end - cursor_dt).total_seconds() // 60)
                    if remaining > 0:
                        rows.append(make_row(
                            rdv, newcomer_name, newcomer_email,
                            mgr1_name, mgr1_email, mgr2_name, mgr2_email,
                            cursor_dt, bl_end, day_date,
                            suffix=" (cont.)", custom_dur=remaining
                        ))
                        rdvs.at[rdv_idx, "Duration"] = dur_min - remaining
                    break
        day_idx += 1

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


# ── helpers ─────────────────────────────────────────────────────
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

def make_row(rdv, new_name, new_email,
             m1_name, m1_email, m2_name, m2_email,
             start_dt, end_dt, day_date,
             suffix="", custom_dur=None):
    return {
        "Newcomer Email": new_email,
        "Newcomer Name":  new_name,
        "Role Group":     rdv["Role"],
        "RDV Title":      f"{rdv['RDV']}{suffix}",
        "RDV Description": rdv["Short RDV Description"],
        "Contact Person1 Email": rdv.get("Contact Person1 Email", ""),
        "Contact Person1 Name":  rdv.get("Contact Person1 Name", ""),
        "Contact Person2 Email": rdv.get("Contact Person2 Email", ""),
        "Contact Person2 Name":  rdv.get("Contact Person2 Name", ""),
        "RDV Date":  day_date.isoformat(),
        "Start Time": start_dt.strftime("%H:%M"),
        "End Time":   end_dt.strftime("%H:%M"),
        "Duration":   custom_dur if custom_dur is not None else int(rdv["Duration"]),
        "Location":   rdv.get("Location", ""),
        "Manager1 Email": m1_email,
        "Manager1 Name":  m1_name,
        "Manager2 Email": m2_email,
        "Manager2 Name":  m2_name,
        "Status": "Planned",
        "Hired Date": day_date.isoformat()
    }


# ────────────────────────────────────────────────────────────────
#  MANUAL RDV MERGE  (priority rows)
# ────────────────────────────────────────────────────────────────
def merge_manual_rdvs(auto_df, manual_df,
                      newcomer_name, newcomer_email,
                      mgr1_name, mgr1_email,
                      mgr2_name, mgr2_email):

    def to_dt(date_str, time_str):
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    # 1. convert manual rows
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

    # 2. detect overlaps
    occupied = [(to_dt(r["RDV Date"], r["Start Time"]),
                 to_dt(r["RDV Date"], r["End Time"])) for _, r in manual_df_clean.iterrows()]

    queue, keep_auto = [], []
    for _, a in auto_df.iterrows():
        a_s, a_e = to_dt(a["RDV Date"], a["Start Time"]), to_dt(a["RDV Date"], a["End Time"])
        if any(not (a_e <= o_s or a_s >= o_e) for o_s, o_e in occupied):
            queue.append(a)
        else:
            keep_auto.append(a)

    if queue:
        q_df   = pd.DataFrame(queue).sort_values(["RDV Date", "Start Time"]).reset_index(drop=True)
        moved  = _reschedule_queue(q_df, occupied)
        keep_auto.extend(moved)

    final_df = pd.concat([manual_df_clean, pd.DataFrame(keep_auto)], ignore_index=True)
    final_df = final_df.sort_values(["RDV Date", "Start Time"]).reset_index(drop=True)
    return final_df


# ----------------------------------------------------------------
#  Mini‑scheduler for queued RDVs  (drops breaks fully covered)
# ----------------------------------------------------------------
def _reschedule_queue(queue_df, occupied):
    moved = []

    def day_idx_of(date0, d):
        return (d - date0).days

    for _, rdv in queue_df.iterrows():
        dur = int(rdv["Duration"])
        cur = datetime.strptime(f"{rdv['RDV Date']} {rdv['Start Time']}", "%Y-%m-%d %H:%M")
        placed = False

        while not placed:
            ref_day = occupied[0][0].date()
            idx     = day_idx_of(ref_day, cur.date())
            d_start, d_end, breaks = day_bounds(idx)

            # ⬇️  remove breaks fully covered by an occupied interval
            breaks = [
                (bs, be) for (bs, be) in breaks
                if not any(
                    o_s.date() == cur.date() and o_s.time() <= bs and be <= o_e.time()
                    for o_s, o_e in occupied
                )
            ]

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
                    new_rdv = rdv.copy()
                    new_rdv["RDV Date"]   = start.date().isoformat()
                    new_rdv["Start Time"] = start.strftime("%H:%M")
                    new_rdv["End Time"]   = end.strftime("%H:%M")
                    occupied.append((start, end))
                    moved.append(new_rdv)
                    placed = True
                    break

            if not placed:
                cur = datetime.combine(cur.date() + timedelta(days=1), time(9, 0))
    return moved
