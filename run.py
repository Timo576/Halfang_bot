"""Farms Halfang in Wizard101. Note the mouse is moved whenever sscreenshots
are taken, so ensure ability to exit without mouse."""

import time
import win32con
import win32api
import win32gui
import win32ui
import numpy as np
from pathlib import Path
from PIL import Image
import cv2

# Define keys
VK_X = 0x58
VK_W = 0x57
VK_D = 0x44
VK_A = 0x41

# Enable debug printing
DEBUG = True
# Screen locations
MOUSE_HOME = (0, 500)
SCREEN_SIZE_BOX = (0, 0, 1920, 1080)
LOADING_SCREEN_BOX = (0, 0, 400, 400)
CARDS_LOCATION = (680, 475, 1330, 610)
CARD_SIZE = (76, 40)
CARD_TOP_SIDE = 499
CARD_LEFT_SIDES = {7: [686, 780, 873, 967, 1061, 1155, 1249],
                   6: [733, 827, 921, 1015, 1109, 1202],
                   5: [780, 873, 967, 1061, 1155],
                   4: [827, 921, 1015, 1108],
                   3: [873, 967, 1061],
                   2: [921, 1015],
                   1: [967]}
PASS_LOCATION = (630, 645, 765, 680)
COMMONS_ICON_LOCATION = (1600, 965, 1620, 990)
QUEST_ARROW_LOCATION = (875, 870, 1050, 985)
# Timers
ALT_TAB_TIME = 1
CARD_LOAD = 0.3
CARD_SELECT_TIME = 0.2
ENCHANT_TIME = 0.5
TIMEOUTS = 300
ANGLE_TIME_CONSTANT = 300


def initialize():
    """Initializes the device contexts and bitmap."""
    hdesktop = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()
    screenshot = win32ui.CreateBitmap()
    return hdesktop, desktop_dc, img_dc, mem_dc, screenshot


def image_to_bitmap_data(image):
    """Reshapes the data to match custom bitmap pixel format,
    reverses the ordering of RGB,
    adds padding byte to each row."""
    test_image = np.array(image).reshape(-1, 3)[:, ::-1]
    new_column = np.full((test_image.shape[0], 1), 255)
    result_array = np.hstack((test_image, new_column))
    return result_array


def bitmap_to_image(bitmap):
    """Converts a bitmap to an image for debugging or saving."""
    bmp_info = bitmap.GetInfo()
    bmp_str = bitmap.GetBitmapBits(True)
    # noinspection PyArgumentEqualDefault
    img = Image.frombuffer(
        'RGB',
        (bmp_info['bmWidth'], bmp_info['bmHeight']),
        bmp_str, 'raw', 'BGRX', 0, 1
    )
    return img


def bytes_to_2d_array(byte_data):
    """Converts byte data to a 2D NumPy array, separating rows by the padding byte."""
    byte_array = np.frombuffer(byte_data, dtype=np.uint8)
    reshaped_array = byte_array.reshape(-1, 4)
    return reshaped_array


def screenshot_area(mem_dc, img_dc, screenshot, locators):
    """Takes a screenshot of the specified area."""
    win32api.SetCursorPos(MOUSE_HOME)  # Move mouse out of the way of anything
    left, top, right, bottom = locators
    width = right - left
    height = bottom - top
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top),
                  win32con.SRCCOPY)
    return screenshot


def cleanup(mem_dc, hdesktop, desktop_dc):
    """Releases resources."""
    mem_dc.DeleteDC()
    win32gui.ReleaseDC(hdesktop, desktop_dc)


def enter_dungeon():
    """Waits for alt-tab then presses X to enter the dungeon."""
    win32api.keybd_event(VK_X, 0, 0, 0)
    win32api.keybd_event(VK_X, 0, win32con.KEYEVENTF_KEYUP, 0)
    if DEBUG:
        print('Pressed X to enter dungeon.')
    return


def is_loading(mem_dc, img_dc, screenshot):
    """Checks if the loading screen is present."""
    loading_screen = screenshot_area(mem_dc, img_dc, screenshot,
                                     LOADING_SCREEN_BOX)
    directory_path = Path('Loading_screens')
    for file_path in directory_path.iterdir():
        old_bitmap = image_to_bitmap_data(Image.open(file_path))
        new_bitmap = bytes_to_2d_array(loading_screen.GetBitmapBits(True))
        if np.array_equal(old_bitmap, new_bitmap):
            if DEBUG:
                print('Loading')
            return True
    if DEBUG:
        print('Not loading')
    return False


def entry_verify(mem_dc, img_dc, screenshot):
    """Verifies that the dungeon is being entered,
    and presses w in loading screen"""
    loop_count = 0
    while not is_loading(mem_dc, img_dc, screenshot):
        if DEBUG:
            print('Waiting for entry loading screen.')
        loop_count += 1
        time.sleep(0.1)
        if loop_count > 150:
            loading_screen_fail = screenshot_area(mem_dc, img_dc, screenshot,
                                                  LOADING_SCREEN_BOX)
            loading_screen_image = bitmap_to_image(loading_screen_fail)
            loading_screen_image.save('Errors/loading_screen_fail.png')
            raise Exception("Loading screen not found.")
    if DEBUG:
        print('Pressing w.')
    win32api.keybd_event(VK_W, 0, 0, 0)  # Press w to exit load running
    while is_loading(mem_dc, img_dc, screenshot):
        time.sleep(0.1)
    return


def check_battle_joined(mem_dc, img_dc, screenshot):
    """Checks if the battle has been joined."""
    loop_count = 0
    while not choosing_phase(img_dc, mem_dc, screenshot):
        print('Looping, to join')
        if loop_count > 600:
            pass_button = screenshot_area(mem_dc, img_dc, screenshot,
                                          PASS_LOCATION)
            pass_button_image = bitmap_to_image(pass_button)
            pass_button_image.save('Errors/pass_button_fail')
            raise Exception("Battle not found.")
        loop_count += 1
        time.sleep(0.1)
    if DEBUG:
        print('Releasing w.')
    # Releasing w to not interfere with battle
    win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)
    return


def choosing_phase(img_dc, mem_dc, screenshot):
    """Determines if in a battle in the choosing phase."""
    pass_reference = Image.open('Battle_icons/pass_button.png')
    pass_button = screenshot_area(mem_dc, img_dc, screenshot,
                                  PASS_LOCATION)
    if np.array_equal(image_to_bitmap_data(pass_reference),
                      bytes_to_2d_array(pass_button.GetBitmapBits(True))):
        if DEBUG:
            print('Choosing phase.')
        time.sleep(CARD_LOAD)  # Wait for cards to load properly
        return True
    if DEBUG:
        print('Not choosing phase.')
    return False


def click(location):
    """Helper to click the mouse in a location with delays so w101 responds"""
    win32api.SetCursorPos(location)
    time.sleep(0.1)  # May need longer if cursor disappears
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    # Potential need to sleep if cursor disappears
    win32api.SetCursorPos(MOUSE_HOME)
    if DEBUG:
        print(f'Click at {location}.')
    return


def cast_meteor(mem_dc, img_dc, screenshot, num_cards=7):
    """Identifies location of a colossal card and a meteor card
    then enchants the meteor and casts."""
    cards = identify_cards(img_dc, mem_dc, screenshot)
    colossal_card = cards.index('Colossal')
    meteor_card = cards.index('Meteor')
    colossal_location = card_locator(num_cards, colossal_card)
    click(colossal_location)
    time.sleep(CARD_SELECT_TIME)
    meteor_location = card_locator(num_cards, meteor_card)
    click(meteor_location)
    time.sleep(ENCHANT_TIME)
    click(enchant_adjust(colossal_card, meteor_card,
                         num_cards))  # Move when enchant
    if DEBUG:
        print('Cast Meteor.')
    time.sleep(1)
    return


def card_locator(num_cards, card):
    """Helper returns the location of a card from the corner."""
    return (CARD_LEFT_SIDES[num_cards][card] + int(CARD_SIZE[0] / 2),
            CARD_TOP_SIDE + int(CARD_SIZE[1] / 2))


def enchant_adjust(sun_spot, cast_spot, num_cards):
    """Shift of spell when enchanted."""
    if sun_spot > cast_spot:
        return card_locator(num_cards - 1, cast_spot)
    return card_locator(num_cards - 1, cast_spot - 1)


def identify_num_cards():
    """Identifies the number of cards in the card area."""
    # TODO: Implement
    pass


def identify_cards(img_dc, mem_dc, screenshot):
    """Identifies the cards in the card area."""
    cards = []
    for card_spot in range(7):
        card_area = screenshot_area(mem_dc, img_dc, screenshot,
                                    (CARD_LEFT_SIDES[7][card_spot],
                                     CARD_TOP_SIDE,
                                     CARD_LEFT_SIDES[7][card_spot] + CARD_SIZE[
                                         0],
                                     CARD_TOP_SIDE + CARD_SIZE[1]))
        colossal_dat = image_to_bitmap_data(Image.open(
            f'Battle_icons/Colossal/7_{card_spot + 1}.png'))
        meteor_dat = image_to_bitmap_data(Image.open(
            f'Battle_icons/Meteor/7_{card_spot + 1}.png'))
        if np.array_equal(colossal_dat,
                          bytes_to_2d_array(card_area.GetBitmapBits(True))):
            cards.append('Colossal')
            if DEBUG:
                print(f'Colossal found at {card_spot + 1}.')
        elif np.array_equal(meteor_dat,
                            bytes_to_2d_array(card_area.GetBitmapBits(True))):
            cards.append('Meteor')
            if DEBUG:
                print(f'Meteor found at {card_spot + 1}.')
        else:
            card_area_image = bitmap_to_image(card_area)
            card_area_image.save(f'Errors/card_fail_at{card_spot + 1}.png')
            cards.append('Unknown')
            if DEBUG:
                print(f'Unknown found at {card_spot + 1}.')
    return cards


def out_of_battle(img_dc, mem_dc, screenshot):
    """Verifies if the battle has ended"""
    commons_reference = Image.open('Battle_icons/commons_icon.png')
    commons_icon = screenshot_area(mem_dc, img_dc, screenshot,
                                   COMMONS_ICON_LOCATION)
    if np.array_equal(image_to_bitmap_data(commons_reference),
                      bytes_to_2d_array(commons_icon.GetBitmapBits(True))):
        if DEBUG:
            print('Out of battle.')
        return True
    if DEBUG:
        print('In battle.')
    return False


def align_quest_arrow(img_dc, mem_dc, screenshot):
    """Aligns the quest arrow to the screen."""
    angle = check_arrow_direction(mem_dc, img_dc, screenshot)
    while abs(angle) > 5:
        angle_time = abs(angle) / ANGLE_TIME_CONSTANT
        if angle < 180:
            win32api.keybd_event(VK_D, 0, 0, 0)
            time.sleep(angle_time)
            win32api.keybd_event(VK_D, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif angle < 0:
            win32api.keybd_event(VK_A, 0, 0, 0)
            time.sleep(angle_time)
            win32api.keybd_event(VK_A, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            raise Exception("Bad arrow angle.")
        angle = check_arrow_direction(mem_dc, img_dc, screenshot)


def exit_dungeon(mem_dc, img_dc, screenshot):
    """Exits the dungeon from first spot."""
    # TODO: Implement a way to exit from any spot
    # align_quest_arrow(img_dc, mem_dc, screenshot)
    # win32api.keybd_event(VK_W, 0, 0, 0)
    # time.sleep(6)
    # win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_W, 0, 0, 0)
    time.sleep(3)
    win32api.keybd_event(VK_D, 0, 0, 0)
    time.sleep(0.3)
    win32api.keybd_event(VK_D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2)
    win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)
    fail_count = 0
    while not is_loading(mem_dc, img_dc, screenshot):
        time.sleep(0.1)
        fail_count += 1
        if DEBUG:
            print('Waiting for exit loading screen.')
        if fail_count > 10:
            raise Exception("Failed to exit dungeon.")
    while is_loading(mem_dc, img_dc, screenshot):
        if DEBUG:
            print('Waiting for exit loading to finish.')
        time.sleep(0.1)
    time.sleep(2)
    if DEBUG:
        print('Exited dungeon.')
    return


def check_arrow_direction(mem_dc, img_dc, screenshot):
    """Check the direction of the arrow in the image."""
    # TODO: Clean up
    quest_arrow = screenshot_area(mem_dc, img_dc, screenshot,
                                  QUEST_ARROW_LOCATION)
    quest_arrow_image = bitmap_to_image(quest_arrow)
    quest_arrow_image.save('Temp/quest_arrow.png')
    image = cv2.imread('Temp/quest_arrow.png')
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 0, 0])
    upper_yellow = np.array([80, 255, 255])
    mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    yellow_filtered_image = cv2.bitwise_and(image, image, mask=mask)
    gray_filtered = cv2.cvtColor(yellow_filtered_image, cv2.COLOR_BGR2GRAY)
    blurred_filtered = cv2.GaussianBlur(gray_filtered, (5, 5), 0)
    contours, _ = cv2.findContours(blurred_filtered, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        hull_mask = np.zeros_like(gray_filtered, dtype=np.uint8)
        cv2.drawContours(hull_mask, [hull], -1, 255, thickness=cv2.FILLED)
        contour_mask = np.zeros_like(gray_filtered, dtype=np.uint8)
        cv2.drawContours(contour_mask, [contour], -1, 255,
                         thickness=cv2.FILLED)
        subtract_mask = cv2.bitwise_and(hull_mask,
                                        cv2.bitwise_not(contour_mask))
        contours_in_subtract_mask, _ = cv2.findContours(subtract_mask,
                                                        cv2.RETR_EXTERNAL,
                                                        cv2.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(contours_in_subtract_mask,
                                 key=cv2.contourArea, reverse=True)
        if len(sorted_contours) >= 2:
            largest_contours = sorted_contours[:2]
            centroid1 = centroid(largest_contours[0])
            centroid2 = centroid(largest_contours[1])
            connect_line = np.array([centroid2[0] - centroid1[0], centroid2[1] - centroid1[1]])
            centroid_main = centroid(contour)
            dir_line = np.array([centroid_main[0] - centroid1[0], centroid_main[1] - centroid1[1]])
            normal = np.array([-connect_line[1], connect_line[0]])
            projected = np.dot(dir_line, normal)
            arrow_direction = normal * projected
            angle = angle_to_straight(arrow_direction)
            # if DEBUG:
            #     print(f'Angle: {angle}, Arrow Direction: {arrow_direction}')
            #     cv2.line(image, centroid_main, (
            #         centroid_main[0] + arrow_direction[0],
            #         centroid_main[1] + arrow_direction[1]), (0, 255, 0), 2)
            #     cv2.circle(image, centroid1, 5, (0, 255, 255), -1)
            #     cv2.circle(image, centroid2, 5, (0, 255, 255), -1)
            #     cv2.circle(image, centroid_main, 5, (0, 255, 255), -1)
            #     cv2.imshow('Final Image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return angle


def angle_to_straight(vector):
    """Converts a vector to the angle it makes with the y-axis,
    with messed up coords"""
    if vector[1] < 0:
        angle = 180 + np.degrees(np.arctan(vector[0] / vector[1]))
    else:
        angle = np.degrees(np.arctan(vector[0]/vector[1]))
    angle = 180-angle
    # convert angle to -180 to 180
    if angle > 180:
        angle -= 360
    return angle


def centroid(contour_):
    """Helper for centroids"""
    moments = cv2.moments(contour_)
    if moments['m00'] == 0:
        return 0, 0
    return int(moments['m10'] / moments['m00']), int(moments['m01'] / moments['m00'])


def pass_battle():
    """Passes the battle."""
    click((PASS_LOCATION[0] + int((PASS_LOCATION[2] - PASS_LOCATION[0]) / 2),
           PASS_LOCATION[1] + int((PASS_LOCATION[3] - PASS_LOCATION[1]) / 2)))
    if DEBUG:
        print('Passed battle.')
    time.sleep(1)
    return


def spam_meteor(mem_dc, img_dc, screenshot):
    """Kills Halfang"""
    while not out_of_battle(img_dc, mem_dc, screenshot):
        if choosing_phase(img_dc, mem_dc, screenshot):
            try:
                cast_meteor(mem_dc, img_dc, screenshot)
            except ValueError:
                if DEBUG:
                    print('Meteor or colossal not found.')
                pass_battle()
        else:
            time.sleep(1)
    return


def main():
    """Enters the dungeon, join the battle, kills Halfang, and leaves the dungeon."""
    # TODO: fails: wrong fight spot, something loading exit, ??. Eventually selling
    # TODO: clean/reorder
    hdesktop, desktop_dc, img_dc, mem_dc, screenshot = initialize()
    try:
        time.sleep(ALT_TAB_TIME)
        runs = 0
        while runs < 50:
            enter_dungeon()
            entry_verify(mem_dc, img_dc, screenshot)
            check_battle_joined(mem_dc, img_dc, screenshot)
            spam_meteor(mem_dc, img_dc, screenshot)
            exit_dungeon(mem_dc, img_dc, screenshot)
            runs += 1
    finally:
        cleanup(mem_dc, hdesktop, desktop_dc)


if __name__ == '__main__':
    main()
