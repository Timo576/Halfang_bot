import timeit
import win32gui
import win32ui
import win32con
from PIL import ImageGrab
import pyautogui
import mss
import cv2
import wx
import numpy as np
import matplotlib.pyplot as plt


def screenshot_wx(locs):
    left, top, right, bottom = locs
    app = wx.App(False)
    screen = wx.ScreenDC()
    bmp = wx.Bitmap(right-left, bottom-top)
    mem = wx.MemoryDC(bmp)
    mem.Blit(0, 0, right-left, bottom-top, screen, left, top)
    mem.SelectObject(wx.NullBitmap)
    img = bmp.ConvertToImage()
    return img

def screenshot_opencv(locs):
    left, top, right, bottom = locs
    img = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return img

def screenshot_mss(locs):
    left, top, right, bottom = locs
    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": right-left, "height": bottom-top}
        img = sct.grab(monitor)
    return img

def screenshot_pyautogui(locs):
    left, top, right, bottom = locs
    img = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
    return img

def screenshot_win32(locs):
    left, top, right, bottom = locs
    hdesktop = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    width = right - left
    height = bottom - top
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)

    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

    mem_dc.DeleteDC()
    win32gui.ReleaseDC(hdesktop, desktop_dc)

    return screenshot

def screenshot_pillow(locs):
    left, top, right, bottom = locs
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    return img


# Define the locations for the screenshot
locs = (100, 100, 500, 500)

# Timeit setup
setup_code = """
from __main__ import screenshot_win32, screenshot_pillow, screenshot_pyautogui, screenshot_mss, screenshot_opencv, screenshot_wx, locs
"""

# Timeit statements
stmt_win32 = "screenshot_win32(locs)"
stmt_pillow = "screenshot_pillow(locs)"
stmt_pyautogui = "screenshot_pyautogui(locs)"
stmt_mss = "screenshot_mss(locs)"
stmt_opencv = "screenshot_opencv(locs)"
stmt_wx = "screenshot_wx(locs)"

repeats = 1
number = 1

times_win32 = timeit.repeat(stmt=stmt_win32, setup=setup_code, number=number, repeat=repeats)
times_mss = timeit.repeat(stmt=stmt_mss, setup=setup_code, number=number, repeat=repeats)
times_wx = timeit.repeat(stmt=stmt_wx, setup=setup_code, number=number, repeat=repeats)
times_pillow = timeit.repeat(stmt=stmt_pillow, setup=setup_code, number=number, repeat=repeats)
times_opencv = timeit.repeat(stmt=stmt_opencv, setup=setup_code, number=number, repeat=repeats)
times_pyautogui = timeit.repeat(stmt=stmt_pyautogui, setup=setup_code, number=number, repeat=repeats)


print("win32:", times_win32)
print("mss:", times_mss)
print("wx:", times_wx)
# plt.plot(times_win32, label="win32")
# plt.plot(times_mss, label="mss")
# plt.plot(times_wx, label="wx")
# plt.plot(times_pillow, label="Pillow")
# plt.plot(times_opencv, label="opencv")
# plt.plot(times_pyautogui, label="pyautogui")
# plt.legend()
# plt.show()

# # Benchmark the methods using perfplot
# perfplot.show(
#     setup=lambda n: (locs,),
#     kernels=[
#         lambda locs: screenshot_win32(locs),
#         lambda locs: screenshot_pillow(locs),
#     ],
#     labels=["win32", "Pillow"],
#     equality_check=None,
#     n_range=[k for k in range(10)],
#     xlabel="num screenshots",
# )
