import ctypes
import ctypes.wintypes
import win32gui
import win32con
import signal
import sys
from win11toast import toast

# Constants
WM_DEVICECHANGE = 0x0219
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004

class DEV_BROADCAST_HDR(ctypes.Structure):
    _fields_ = [
        ("dbch_size", ctypes.wintypes.DWORD),
        ("dbch_devicetype", ctypes.wintypes.DWORD),
        ("dbch_reserved", ctypes.wintypes.DWORD)
    ]

def handle_event(event_type):
    if event_type == DBT_DEVICEARRIVAL:
        print("Audio device connected")
        toast("test", "Device connected", duration="short")
    elif event_type == DBT_DEVICEREMOVECOMPLETE:
        print("Audio device disconnected")
        toast("test", "Device disconnected", duration="short")

def win_proc(hwnd, msg, wparam, lparam):
    if msg == WM_DEVICECHANGE:
        print(f"WM_DEVICECHANGE received: wparam={wparam}")
        handle_event(wparam)
    return 1

def monitor_audio_devices():
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = win_proc
    wc.lpszClassName = 'DeviceChangeMonitor'
    wc.hInstance = win32gui.GetModuleHandle(None)
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(class_atom, 'DeviceChangeMonitor', 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)

    print("Monitoring audio devices...")

    # Set up signal handler for Ctrl+C
    def signal_handler(sig, frame):
        print("Exiting...")
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    win32gui.PumpMessages()

if __name__ == "__main__":
    monitor_audio_devices()