from datetime import datetime, timezone, timedelta

def iso_to_vn_datetime(iso_time_str):
    """
    Chuyển chuỗi ISO thành datetime với timezone UTC+7.
    Nếu chuỗi không có thông tin timezone thì mặc định là UTC+7.
    """
    dt = datetime.fromisoformat(iso_time_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
    else:
        dt = dt.astimezone(timezone(timedelta(hours=7)))
    return dt

def compare_datetime(now, last_follow_up):
    """
    So sánh hai đối tượng datetime.
    Trả về hiệu now - last follow up.
    """
    return now - last_follow_up

def timedelta_to_seconds(td):
    """
    Chuyển đổi một đối tượng timedelta thành số giây (float).
    """
    return td.total_seconds()