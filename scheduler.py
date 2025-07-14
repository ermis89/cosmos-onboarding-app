from datetime import datetime, timedelta
import pandas as pd

def generate_schedule(start_date_str, rdvs):
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    schedule = []
    day_offset = 0
    rdv_index = 0

    while rdv_index < len(rdvs):
        current_date = start_date + timedelta(days=day_offset)
        if current_date.weekday() >= 5:
            day_offset += 1
            continue

        if day_offset == 0:
            work_start = datetime.combine(current_date, datetime.strptime("10:00", "%H:%M").time())
            work_end = datetime.combine(current_date, datetime.strptime("18:00", "%H:%M").time())
            breaks = [
                (datetime.combine(current_date, datetime.strptime("11:30", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("12:00", "%H:%M").time())),
                (datetime.combine(current_date, datetime.strptime("13:00", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("14:00", "%H:%M").time())),
                (datetime.combine(current_date, datetime.strptime("15:30", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("16:00", "%H:%M").time())),
            ]
        else:
            work_start = datetime.combine(current_date, datetime.strptime("09:00", "%H:%M").time())
            work_end = datetime.combine(current_date, datetime.strptime("17:00", "%H:%M").time())
            breaks = [
                (datetime.combine(current_date, datetime.strptime("10:30", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("11:00", "%H:%M").time())),
                (datetime.combine(current_date, datetime.strptime("13:00", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("14:00", "%H:%M").time())),
                (datetime.combine(current_date, datetime.strptime("15:30", "%H:%M").time()), datetime.combine(current_date, datetime.strptime("16:00", "%H:%M").time())),
            ]

        current_time = work_start
        day_plan = []

        while rdv_index < len(rdvs):
            rdv = rdvs[rdv_index]
            duration = rdv['Duration']
            remaining = duration
            full_title = rdv['RDV']
            contact1 = rdv.get('Contact Person1 Name', '')
            contact2 = rdv.get('Contact Person2 Name', '')
            email1 = rdv.get('Contact Person1 Email', '')
            email2 = rdv.get('Contact Person2 Email', '')

            while remaining > 0:
                if any(b_start <= current_time < b_end for b_start, b_end in breaks):
                    current_time = next(b_end for b_start, b_end in breaks if b_start <= current_time < b_end)
                    continue

                future_breaks = [b_start for b_start, _ in breaks if b_start > current_time]
                if not future_breaks and current_time >= work_end:
                    break

                next_boundary = min(future_breaks + [work_end])
                available = int((next_boundary - current_time).total_seconds() / 60)

                if available <= 0:
                    current_time = next_boundary
                    continue

                chunk = min(remaining, available)
                rdv_start = current_time
                rdv_end = current_time + timedelta(minutes=chunk)

                day_plan.append({
                    "Day": current_date.strftime("%d/%m/%Y"),
                    "Role": rdv['Role'],
                    "RDV": full_title + (" (cont.)" if remaining != duration else ""),
                    "Short RDV Description": rdv['Short RDV Description'],
                    "Contact Person": contact1,
                    "Contact Person Email": email1,
                    "Contact Person 2": contact2,
                    "Contact Person 2 Email": email2,
                    "Duration (minutes)": chunk,
                    "Start Time": rdv_start.strftime("%H:%M"),
                    "End Time": rdv_end.strftime("%H:%M"),
                    "Location": rdv['Location'],
                    "Order": rdv['Order']
                })

                current_time = rdv_end
                remaining -= chunk

                if current_time >= work_end:
                    break

            if remaining > 0:
                break
            else:
                rdv_index += 1

        schedule.extend(day_plan)
        day_offset += 1

    return pd.DataFrame(schedule)
