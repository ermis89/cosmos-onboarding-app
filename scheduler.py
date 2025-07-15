import pandas as pd
from datetime import datetime, timedelta, time

# ────────────────────────────────────────────────────────────────
#  Day template
# ────────────────────────────────────────────────────────────────
def day_bounds(day_idx: int):
    """Return (start, end, breaks) tuple for given 0‑based day index."""
    if day_idx == 0:  # Day‑1
        start, end = time(10, 0), time(18, 0)
        breaks = [
            (time(11, 30), time(12, 0)),
            (time(13, 30), time(14, 30)),  # shifted lunch
            (time(15, 30), time(16, 0)),
        ]
    else:             # Day‑2+
        start, end = time(9, 0), time(17, 0)
        breaks = [
            (time(10, 30), time(11, 0)),
            (time(13, 0),  time(14, 0)),
            (time(15, 30), time(16, 0)),
        ]
    return start, end, breaks


# ────────────────────────────────────────────────────────────────
#  Auto‑generate schedule (no splitting)
# ────────────────────────────────────────────────────────────────
def generate_schedule(df_template: pd.DataFrame,
                      role: str,
                      hire_date,
                      newcom_name: str, newcom_email: str,
                      mgr1_name: str, mgr1_email: str,
                      mgr2_name: str = "", mgr2_email: str = "") -> pd.DataFrame:

    if isinstance(hire_date, datetime):
        hire_date = hire_date.date()

    rdvs = (df_template[df_template["Role"].str.strip() == role.strip()]
            .sort_values("Order")
            .reset_index(drop=True))

    if rdvs.empty:
        raise ValueError(
            f"No template rows found for role '{role}'. "
            f"Available roles: {df_template['Role'].unique().tolist()}"
        )

    rows, day_idx, rdv_idx = [], 0, 0
    while rdv_idx < len(rdvs):

        # skip weekend
        day_date = hire_date + timedelta(days=day_idx)
        while day_date.weekday() >= 5:  # Sat/Sun
            day_idx += 1
            day_date = hire_date + timedelta(days=day_idx)

        day_start, day_end, breaks = day_bounds(day_idx)

        # build blocks
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
                    break  # whole RDV moves to next block/day
        day_idx += 1

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


# ────────────────────────────────────────────────────────────────
#  Merge manager‑priority RDVs (same as before)
#  ...  (no change to code you already have below) ...
# ────────────────────────────────────────────────────────────────
#  Keep the rest of the file exactly as in your current version
#  (merge_manual_rdvs, _reschedule_queue, make_row, OUTPUT_COLS)
# ────────────────────────────────────────────────────────────────
