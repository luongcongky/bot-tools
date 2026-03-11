import datetime
import shutil

def get_time(format="%Y-%m-%d %H:%M:%S", **kwargs):
    """
    Trả về thời gian hiện tại của hệ thống.
    - format: Định dạng thời gian (mặc định YYYY-MM-DD HH:mm:ss)
    """
    now = datetime.datetime.now()
    time_str = now.strftime(format)
    return f"🕒 Thời gian hệ thống hiện tại: {time_str}"

def check_disk(user_input=None):
    """Kiểm tra dung lượng ổ cứng trên WSL/Linux"""
    total, used, free = shutil.disk_usage("/")
    # Chuyển đổi sang GB cho dễ đọc
    return (f"Ổ cứng hệ thống: Tổng {total // (2**30)}GB, "
            f"Đã dùng {used // (2**30)}GB, "
            f"Còn trống {free // (2**30)}GB.")
