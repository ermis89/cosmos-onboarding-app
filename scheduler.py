import pandas as pd
from datetime import datetime, timedelta, time

# ── day template ────────────────────────────────────────────────
def day_bounds(day_idx: int):
    """Return work-day start, end, and break windows for a 0-based day index."""
    if day_idx == 0:                                   # Day-1 template
        start = time(10, 0)
        end   = time(18, 0)
        breaks = [
            (time(11, 30), time(12,  0)),   # coffee
            (time(13, 30), time(14, 30)),   # ⬅️  shifted 30 min later
            (time(15, 30), time(16,  0)),   # coffee
        ]
    else:                                              # Day-2+
        start = time( 9, 0)
        end   = time(17, 0)
        breaks = [
            (time(10, 30), time(11,  0)),
            (time(13,  0), time(14,  0)),
            (time(15, 30), time(16,  0)),
        ]
    return start, end, breaks



# ── public API ──────────────────────────────────────────────────
def generate_schedule(
        df_template: pd.DataFrame,
        role: str,
        hire_date,                                    # datetime.date or datetime
        newcomer_name: str,
        newcomer_email: str,
        mgr1_name: str, mgr1_email: str,
        mgr2_name: str = "", mgr2_email: str = ""
) -> pd.DataFrame:
    """
    Build full schedule for the given role & hire date.
    Returns a DataFrame with the 20 required columns.
    """

    # ensure hire_date is a datetime.date
    if isinstance(hire_date, datetime):
        hire_date = hire_date.date()

    # filter & clean template rows
    rdvs = (df_template[df_template["Role"].str.strip() == role.strip()]
            .sort_values("Order")
            .reset_index(drop=True))

    if rdvs.empty:
        return pd.DataFrame()              # nothing to schedule

    rows = []
    day_idx = 0
    rdv_idx = 0

    while rdv_idx < len(rdvs):

        # skip weekends
        day_date = hire_date + timedelta(days=day_idx)
        while day_date.weekday() >= 5:      # 5,6 = Sat, Sun
            day_idx += 1
            day_date = hire_date + timedelta(days=day_idx)

        # build day blocks
        day_start, day_end, breaks = day_bounds(day_idx)
        blocks = []
        cursor = datetime.combine(day_date, day_start)
        for bs, be in breaks + [(day_end, day_end)]:   # final virtual block
            blocks.append((cursor, datetime.combine(day_date, bs)))
            cursor = datetime.combine(day_date, be)

        # fill blocks
        for block_start, block_end in blocks:
            cursor_dt = block_start

            while rdv_idx < len(rdvs):
                rdv = rdvs.loc[rdv_idx]
                dur_min = int(rdv["Duration"])
                rdv_end = cursor_dt + timedelta(minutes=dur_min)

                # fits entirely
                if rdv_end <= block_end:
                    rows.append(make_row(
                        rdv, newcomer_name, newcomer_email,
                        mgr1_name, mgr1_email, mgr2_name, mgr2_email,
                        cursor_dt, rdv_end, day_date
                    ))
                    cursor_dt = rdv_end
                    rdv_idx += 1
                else:
                    # partial fits? split & continue next slot
                    remaining = int((block_end - cursor_dt).total_seconds() // 60)
                    if remaining > 0:
                        rows.append(make_row(
                            rdv, newcomer_name, newcomer_email,
                            mgr1_name, mgr1_email, mgr2_name, mgr2_email,
                            cursor_dt, block_end, day_date,
                            suffix=" (cont.)", custom_dur=remaining
                        ))
                        rdvs.at[rdv_idx, "Duration"] = dur_min - remaining
                    break  # move to next block

        day_idx += 1    # next calendar day

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


def make_row(
        rdv, new_name, new_email,
        m1_name, m1_email, m2_name, m2_email,
        start_dt: datetime, end_dt: datetime, day_date,
        suffix: str = "", custom_dur: int | None = None):
    """Return a single schedule row dictionary."""
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
#  MANUAL RDV MERGE  (priority rows)                             │
# ────────────────────────────────────────────────────────────────
def merge_manual_rdvs(auto_df: pd.DataFrame,
                      manual_df: pd.DataFrame,
                      newcomer_name: str,
                      newcomer_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str, mgr2_email: str) -> pd.DataFrame:
    """
    Convert manual_df rows to the 20‑column format and prepend them
    to auto_df, removing any auto‑generated rows that overlap.
    """

    def parse_dt(d, tstr):
        hh, mm = map(int, tstr.split(":"))
        return datetime.combine(pd.to_datetime(d).date(), time(hh, mm))

    manual_rows = []
    for _, row in manual_df.iterrows():
        start_dt = parse_dt(row["Date"], row["Start"])
        end_dt   = parse_dt(row["Date"], row["End"])

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
            "RDV Date":  start_dt.date().isoformat(),
            "Start Time": start_dt.strftime("%H:%M"),
            "End Time":   end_dt.strftime("%H:%M"),
            "Duration":   int((end_dt - start_dt).seconds // 60),
            "Location":   "",
            "Manager1 Email": mgr1_email,
            "Manager1 Name":  mgr1_name,
            "Manager2 Email": mgr2_email,
            "Manager2 Name":  mgr2_name,
            "Status": "Planned (manual)",
            "Hired Date": start_dt.date().isoformat()
        })

    manual_df_clean = pd.DataFrame(manual_rows)

    # ── remove auto rows that clash with manual ones
    def overlaps(a_row):
        a_start = datetime.strptime(f"{a_row['RDV Date']} {a_row['Start Time']}",
                                    "%Y-%m-%d %H:%M")
        a_end   = datetime.strptime(f"{a_row['RDV Date']} {a_row['End Time']}",
                                    "%Y-%m-%d %H:%M")
        for _, m in manual_df_clean.iterrows():
            m_start = datetime.strptime(f"{m['RDV Date']} {m['Start Time']}",
                                        "%Y-%m-%d %H:%M")
            m_end   = datetime.strptime(f"{m['RDV Date']} {m['End Time']}",
                                        "%Y-%m-%d %H:%M")
            if a_row['RDV Date'] == m['RDV Date'] and not (a_end <= m_start or a_start >= m_end):
                return True
        return False

    auto_df_non_overlap = auto_df[~auto_df.apply(overlaps, axis=1)]

    # final ordered df: manual first (priority) + remaining auto
    final_df = pd.concat([manual_df_clean, auto_df_non_overlap], ignore_index=True)
    final_df = final_df.sort_values(["RDV Date", "Start Time"]).reset_index(drop=True)
    return final_df
