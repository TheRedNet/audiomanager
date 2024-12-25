import win32gui
import win32api
import win32con
import win32process


def islocked():
    _, pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())

    try:
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
        filename = win32process.GetModuleFileNameEx(handle, 0)
    except Exception as _e:
        filename = "LockApp.exe"
        del _e

    current_status = "LockApp" in filename
    return current_status
