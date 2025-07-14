from datetime import datetime, timedelta
import pandas as pd


def generate_schedule(start_date_str, rdvs):
    """
    Build full onboarding schedule (beyond 5 days if needed).
    Returns a pandas DataFrame ready to display / export.
    """

    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    schedule = []
    day_offset = 0
    rdv_index = 0

    while rdv_index < len(rdvs):
        current_date = start_date + timedelta(days=day_offset)

        # Skip weekends
        if current_date.weekday() >= 5:
            day_offset += 1
            continue

        # Day-type configuration
        if day_offset == 0:
            work_start = datetime.combine(current_date, datetime.strptime("10:00", "%H:%M").time())
            work_end   = datetime.combine(current_date, datetime.strptime("18:00", "%H:%M").time())
            breaks = [
                (datetime.combine(current_date, datetime.strptime("11:30", "%H:%M").time()),
                 datetime.combine(current_date, datetime.strptime("12:00", "%H:%M").time())),
        ]
        else:
            work_start = datetime.combine(current_date, datetime.strptime("09:00", "%H:%M").time())
            work_end   = datetime.combine(current_date, datetime.strptime("17:00", "%H:%M").time())
            breaks = [
                (datetime.combine(current_date, datetime.strptime("10:30", "%H:%M").time()),
                 datetime.combine(current_date, datetime.strptime("11:00", "%H:%M").time())),
        ]
        # common breaks (same for all days)
        breaks += [
            (datetime.combine(current_date, datetime.strptime("13:00", "%H:%M").time()),
             datetime.combine(current_date, datetime.strptime("14:00", "%H:%M").time())),
            (datetime.combine(current_date, datetime.strptime("15:30", "%H:%M").time()),
             datetime.combine(current_date, datetime.strptime("16:00", "%H:%M").time())),
        ]

        current_time = work_start
        day_plan = []

        # fill the day
        while rdv_index < len(rdvs):
            rdv = rdvs[rdv_index]
            remaining = int(rdv["Duration"])
            first_chunk = True

            while remaining > 0:
                # jump over break if we're inside one
                inside_break = next((b for b in breaks if b[0] <= current_time < b[1]), None)
                if inside_break:
                    current_time = inside_break[1]
                    continue

                # next boundary
                future_breaks = [b[0] for b in breaks if b[0] > current_time]
                boundary = min(future_breaks + [work_end])
                available = int((boundary - current_time).total_seconds() / 60)

                if available <= 0:
                    break  # out of working time—spill to next day

                chunk = min(remaining, available)
                rdv_start = current_time
                rdv_end   = current_time + timedelta(minutes=chunk)

                day_plan.append({
                    "Day": current_date.strftime("%d/%m/%Y"),
                    "Role": rdv["Role"],
                    "RDV": rdv["RDV"] + (" (cont.)" if not first_chunk else ""),
                    "Short RDV Description": rdv["Short RDV Description"],
                    "Contact Person": rdv.get("Contact Person1 Name", ""),
                    "Contact Person Email": rdv.get("Contact Person1 Email", ""),
                    "Contact Person 2": rdv.get("Contact Person2 Name", ""),
                    "Contact Person 2 Email": rdv.get("Contact Person2 Email", ""),
                    "Duration (minutes)": chunk,
                    "Start Time": rdv_start.strftime("%H:%M"),
                    "End Time": rdv_end.strftime("%H:%M"),
                    "Location": rdv["Location"],
                    "Order": rdv["Order"],
                })

                current_time = rdv_end
                remaining -= chunk
                first_chunk = False

            # if part of RDV left, break out to spill next day
            if remaining > 0:
                rdvs[rdv_index]["Duration"] = remaining
                break
            else:
                rdv_index += 1

        schedule.extend(day_plan)
        day_offset += 1

    return pd.DataFrame(schedule)
