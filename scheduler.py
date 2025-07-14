import pandas as pd
from datetime import timedelta

def generate_schedule(df_template, role, start_date, newcomer_name, newcomer_email, manager1_name, manager1_email, manager2_name, manager2_email):
    df_role = df_template[df_template["Role"] == role].copy()
    df_role.reset_index(drop=True, inplace=True)
    
    current_day = start_date
    daily_start = pd.to_datetime("10:00", format="%H:%M")
    current_time = daily_start

    rdv_dates = []
    start_times = []
    end_times = []
    
    for _, row in df_role.iterrows():
        duration_min = int(row["Duration"])
        rdv_start = current_time
        rdv_end = rdv_start + timedelta(minutes=duration_min)

        # Add break if needed
        if rdv_end.time() > pd.to_datetime("18:00", format="%H:%M").time():
            current_day += timedelta(days=1)
            current_time = pd.to_datetime("09:00", format="%H:%M")
            rdv_start = current_time
            rdv_end = rdv_start + timedelta(minutes=duration_min)

        rdv_dates.append(current_day.strftime("%Y-%m-%d"))
        start_times.append(rdv_start.strftime("%H:%M"))
        end_times.append(rdv_end.strftime("%H:%M"))
        current_time = rdv_end

    df_role["Newcomer Email"] = newcomer_email
    df_role["Newcomer Name"] = newcomer_name
    df_role["Role Group"] = role
    df_role["RDV Title"] = df_role["RDV"]
    df_role["RDV Description"] = df_role["Short RDV Description"]
    df_role["RDV Date"] = rdv_dates
    df_role["Start Time"] = start_times
    df_role["End Time"] = end_times
    df_role["Manager1 Name"] = manager1_name
    df_role["Manager1 Email"] = manager1_email
    df_role["Manager2 Name"] = manager2_name if manager2_name else "None"
    df_role["Manager2 Email"] = manager2_email if manager2_email else "None"
    df_role["Status"] = "Planned"
    df_role["Hired Date"] = start_date.strftime("%Y-%m-%d")

    # Fill contact person columns if missing
    for col in ["Contact Person1 Email", "Contact Person1 Name", "Contact Person2 Email", "Contact Person2 Name"]:
        if col not in df_role.columns:
            df_role[col] = "None"

    columns = ["Newcomer Email", "Newcomer Name", "Role Group", "RDV Title", "RDV Description",
               "Contact Person1 Email", "Contact Person1 Name", "Contact Person2 Email", "Contact Person2 Name",
               "RDV Date", "Start Time", "End Time", "Duration", "Location",
               "Manager1 Email", "Manager1 Name", "Manager2 Email", "Manager2 Name", "Status", "Hired Date"]
    
    return df_role[columns]
