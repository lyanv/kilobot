import time
from collections import deque
from datetime import datetime, timedelta

from settings import LIMITS, REQUEST_COOLING_PERIOD_SEC, tz
from storage.database import db


def cooldown(user_id, user_req_tss=None):
    if user_req_tss is None:
        user_req_tss = {}
    now = time.time()
    if user_id not in user_req_tss:
        user_req_tss[user_id] = now
        return False

    time_since_req = now - user_req_tss[user_id]
    if time_since_req < REQUEST_COOLING_PERIOD_SEC:
        return True

    user_req_tss[user_id] = now
    return False


async def get_user_info(user_id: int):
    user_data = await db.collection("users").document(str(user_id)).get()

    if user_data.exists:
        return user_data.to_dict()
    else:
        return None


async def set_user_limits(user_id: int, status: str, user_name: str, user_fullname: str):
    doc_data = {
        "user_name": user_name,
        "user_fullname": user_fullname,
        "status": status,
        'action_ts': datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    }
    limits = LIMITS.get(status)
    doc_data.update(limits)
    await db.collection('users').document(str(user_id)).set(doc_data)


def create_reply_noreqs(limits):
    reset_time = limits.get("reset_time", None)
    time_until_reset = reset_time - time.time()
    minutes, seconds = divmod(time_until_reset, 60)
    if minutes > 0:
        time_remaining_text = f"{minutes} минут(ы) и {seconds} секунд(ы)"
    else:
        time_remaining_text = f"{seconds} секунд(ы)"

    return f"Ждите {time_remaining_text}."


async def check_limits(user_id, db_user_data):
    daily_limit = db_user_data.get("limit_daily", None)
    weekly_limit = db_user_data.get("limit_weekly", None)
    daily_requests = deque(maxlen=daily_limit)
    weekly_requests = deque(maxlen=weekly_limit)

    saved_daily_requests = db_user_data.get("daily_requests", [])
    saved_weekly_requests = db_user_data.get("weekly_requests", [])

    if saved_daily_requests == [] or saved_weekly_requests == []:
        return None

    for request in saved_daily_requests:
        daily_requests.append(request)
    for request in saved_weekly_requests:
        weekly_requests.append(request)

    now = datetime.now(tz)

    dr = tz.localize(datetime.strptime(daily_requests[0], "%Y-%m-%d %H:%M:%S"))
    wr = tz.localize(datetime.strptime(weekly_requests[0], "%Y-%m-%d %H:%M:%S"))

    while daily_requests and now - dr > timedelta(days=1):
        daily_requests.popleft()
    while weekly_requests and now - wr > timedelta(weeks=1):
        weekly_requests.popleft()

    await db.collection('users').document(str(user_id)).update({
        "daily_requests": list(daily_requests),
        "weekly_requests": list(weekly_requests)
    })

    if db_user_data.get("status") != "unlimited":
        if len(daily_requests) >= daily_limit or len(weekly_requests) >= weekly_limit:
            return f"Превышен лимит запросов"
    else:
        return None


async def update_request_data(user_id):
    user_doc = db.collection('users').document(str(user_id))
    db_user_data = await user_doc.get()
    daily_limit = db_user_data.get("limit_daily")
    weekly_limit = db_user_data.get("limit_weekly")
    user_doc.update({
        "last_request_ts": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    })

    current_daily_requests = db_user_data.to_dict().get('daily_requests', [])
    current_daily_requests.append(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"))
    current_weekly_requests = db_user_data.to_dict().get('weekly_requests', [])
    current_weekly_requests.append(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"))

    if db_user_data.get("status") == "unlimited":
        daily_limit = 5
        weekly_limit = 5

    if len(current_daily_requests) > daily_limit:
        current_daily_requests.pop(0)

    if len(current_weekly_requests) > weekly_limit:
        current_weekly_requests.pop(0)

    await user_doc.update({
        "daily_requests": current_daily_requests,
        "weekly_requests": current_weekly_requests
    })
