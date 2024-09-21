"""Setup calibration images."""

from run import *

# My settings
# 1920 x 1080, fullscreen, regular UI size, high texture detail,
# hardware cursor on
# Bloom off, shadows off, smoothing off, jewel effects off, classic mode
# Particles and brightness default, 2d combat display, quest helper on


def setup_initialize():
    """Initialization for setup functions."""
    time.sleep(ALT_TAB_TIME)
    win32api.SetCursorPos(MOUSE_HOME)
    hdesktop, desktop_dc, img_dc, mem_dc, screenshot = initialize()
    return desktop_dc, hdesktop, img_dc, mem_dc, screenshot


def save_loading_screen():
    """Saves the loading screen as a PNG image."""
    hdesktop, desktop_dc, img_dc, mem_dc, screenshot = setup_initialize()
    enter_dungeon()
    loading_screen = screenshot_area(mem_dc, img_dc, screenshot,
                                     LOADING_SCREEN_BOX)
    directory_path = Path('Loading_screens')
    # Checks if the image is already saved
    for file_path in directory_path.iterdir():
        old_bitmap = image_to_bitmap_data(Image.open(file_path))
        new_bitmap = bytes_to_2d_array(loading_screen.GetBitmapBits(True))
        if np.array_equal(old_bitmap, new_bitmap):
            if DEBUG:
                print('Duplicate image found.')
            cleanup(mem_dc, hdesktop, desktop_dc)
            return
    loading_screen_image = bitmap_to_image(loading_screen)
    file_count = sum(
        1 for entry in Path(directory_path).iterdir() if
        entry.is_file())
    loading_screen_image.save(
        f'Loading_screens/loading_screen{file_count + 1}.png')
    cleanup(mem_dc, hdesktop, desktop_dc)
    return


def save_pass_image():
    """Saves the pass button as a PNG image."""
    desktop_dc, hdesktop, img_dc, mem_dc, screenshot = setup_initialize()
    bitmap_to_image(
        screenshot_area(mem_dc, img_dc, screenshot, PASS_LOCATION)).save(
        'Battle_icons/pass_button.png')
    cleanup(mem_dc, hdesktop, desktop_dc)
    return


def check_card_vision():
    """Saves the card area as a PNG image."""
    desktop_dc, hdesktop, img_dc, mem_dc, screenshot = setup_initialize()
    cards = bitmap_to_image(
        screenshot_area(mem_dc, img_dc, screenshot,
                        CARDS_LOCATION))  # (680, 475, 1330, 610)
    cards.save('Verify_screens/cards.png')
    cleanup(mem_dc, hdesktop, desktop_dc)
    return


def get_cards(num, card_name):
    """Saves cards in each spot"""
    # 5 or 7 cards can be used to find the complete space as all others are duplicates
    desktop_dc, hdesktop, img_dc, mem_dc, screenshot = setup_initialize()
    for card_spot in range(num):
        identifier = f'{card_name}/{num}_{card_spot + 1}'
        card_base = screenshot_area(mem_dc, img_dc, screenshot,
                                    (CARD_LEFT_SIDES[num][card_spot],
                                     CARD_TOP_SIDE,
                                     CARD_LEFT_SIDES[num][card_spot] +
                                     CARD_SIZE[
                                         0],
                                     CARD_TOP_SIDE + CARD_SIZE[1]))
        card_img = bitmap_to_image(card_base)
        card_img.save(f'Battle_icons/{identifier}.png')
        card_base = screenshot_area(mem_dc, img_dc, screenshot,
                                    (CARD_LEFT_SIDES[num][card_spot],
                                     CARD_TOP_SIDE,
                                     CARD_LEFT_SIDES[num][card_spot] +
                                     CARD_SIZE[
                                         0],
                                     CARD_TOP_SIDE + CARD_SIZE[1]))
        card_img = bitmap_to_image(card_base)
        card_img.save(f'Battle_icons/{identifier}dupe.png')
    cleanup(mem_dc, hdesktop, desktop_dc)
    for card_spot in range(num):
        identifier = f'{card_name}/{num}_{card_spot + 1}'
        card_base = Image.open(f'Battle_icons/{identifier}.png')
        card_dupe = Image.open(f'Battle_icons/{identifier}dupe.png')
        if not np.array_equal(image_to_bitmap_data(card_base),
                              image_to_bitmap_data(card_dupe)):
            raise Exception(f'{identifier} not equal.')
        else:
            Path(f'Battle_icons/{identifier}dupe.png').unlink()
    return


def get_commons_icon():
    """Saves the icon to go to commons (for end battle)"""
    desktop_dc, hdesktop, img_dc, mem_dc, screenshot = setup_initialize()
    commons_icon = screenshot_area(mem_dc, img_dc, screenshot,
                                   COMMONS_ICON_LOCATION)
    commons_img = bitmap_to_image(commons_icon)
    commons_img.save('Battle_icons/commons_icon.png')
    cleanup(mem_dc, hdesktop, desktop_dc)
    return


def setup_main():
    """Main wrapper for functions"""
    # save_loading_screen()
    # save_pass_image()
    # check_card_vision()
    # get_cards(1, 'Meteor')
    # get_commons_icon()


if __name__ == '__main__':
    setup_main()
