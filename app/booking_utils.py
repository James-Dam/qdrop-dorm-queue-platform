from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def generate_time_slot_groups(availability_check, item_id):
    early_morning = []
    morning = []
    afternoon = []
    evening = []

    for hour in range(24):
        for minute in [0, 30]:
            time_obj = datetime.strptime(f"{hour:02}:{minute:02}", "%H:%M")
            db_time = time_obj.strftime("%H:%M")
            start_time = time_obj.strftime("%I:%M %p")
            end_time = (time_obj + timedelta(minutes=30)).strftime("%I:%M %p")
            time_slot_dict = {
                "db_value": db_time,
                "display_value": f"{start_time} - {end_time}",
                "available": availability_check(item_id, db_time),
            }

            if hour < 6:
                early_morning.append(time_slot_dict)
            elif hour < 12:
                morning.append(time_slot_dict)
            elif hour < 18:
                afternoon.append(time_slot_dict)
            else:
                evening.append(time_slot_dict)

    return {
        "early_morning": early_morning,
        "morning": morning,
        "afternoon": afternoon,
        "evening": evening,
    }


def local_time_to_utc_datetime(time_slot, time_zone):
    user_tz = ZoneInfo(time_zone)
    today_in_user_tz = datetime.now(user_tz).date()
    local_time = datetime.strptime(time_slot, "%H:%M").time()
    local_datetime = datetime.combine(today_in_user_tz, local_time, tzinfo=user_tz)
    booking_time_utc = local_datetime.astimezone(ZoneInfo("UTC"))
    return booking_time_utc
