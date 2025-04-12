import win32gui
import win32api
import win32con
import win32process
import logging

logger = logging.getLogger("islocked")

def islocked():
    _, pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())

    try:
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
        filename = win32process.GetModuleFileNameEx(handle, 0)
    except Exception as _e:
        logger.error("Failed to get Process Name of Foreground Window: %s", _e)
        if "(5," in str(_e):
            # Access Denied
            filename = ""
        else:
            filename = "LockApp.exe"
        del _e

    current_status = "LockApp" in filename
    return current_status

if __name__ == "__main__":
    import time
    prev_app = 0
    while True:
        _, pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())

        try:
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
            filename = win32process.GetModuleFileNameEx(handle, 0)
        except Exception as e:
            filename = "LockApp.exe"
            print("Error: ", e)
            del e

        current_status = "LockApp" in filename
        if pid != prev_app:
            prev_app = pid
            print(f"Current status: {current_status} filename: {filename} pid: {pid} time: {time.asctime(time.localtime())}")
        time.sleep(0.5)
        
