"""Testing ground for random shit"""

from setup import *


def save_bitmap(bitmap, file_path):
    """Test helper, saves a PyCBitmap to a file using pickle."""
    bmp_info = bitmap.GetInfo()
    bmp_str = bitmap.GetBitmapBits(True)
    with open(file_path, 'wb') as f:
        pickle.dump((bmp_info, bmp_str), f)
    return


def load_bitmap(file_path):
    """Test helper, loads a PyCBitmap from a file using pickle."""
    with open(file_path, 'rb') as f:
        bmp_info, bmp_str = pickle.load(f)
    return bmp_str


def get_screen(location=SCREEN_SIZE_BOX):
    hdesktop, desktop_dc, img_dc, mem_dc, screenshot = setup_initialize()
    test = bitmap_to_image(screenshot_area(mem_dc, img_dc, screenshot, location))
    cleanup(mem_dc, hdesktop, desktop_dc)
    return test


def check_duplicate_images(directory_path):
    """Check if any two images in the directory are the same."""
    images = []
    set_list = []
    for file_path in Path(directory_path).iterdir():
        if file_path.is_file() and file_path.suffix == '.png':
            images.append((file_path, np.array(Image.open(file_path))))
    for index, image in enumerate(images):
        if any(image[0].stem in set_ for set_ in set_list):
            continue
        current_list = [image[0].stem]
        for image2 in images[index+1:]:
            if np.array_equal(image[1], image2[1]):
                current_list.append(image2[0].stem)
        if len(current_list) > 1:
            set_list.append(current_list)
    with open(f'{Path(directory_path).stem}_dupes', 'w') as file:
        for set_ in set_list:
            file.write(f'{set_}\n')


def gen_test():
    """Main wrapper for functions"""
    hdesktop, desktop_dc, img_dc, mem_dc, screenshot = setup_initialize()
    align_quest_arrow(img_dc, mem_dc, screenshot)
    # win32api.keybd_event(VK_W, 0, 0, 0)
    # time.sleep(3)
    # win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)
    # align_quest_arrow(img_dc, mem_dc, screenshot)
    # win32api.keybd_event(VK_W, 0, 0, 0)
    # time.sleep(3)
    # win32api.keybd_event(VK_W, 0, win32con.KEYEVENTF_KEYUP, 0)
    cleanup(mem_dc, hdesktop, desktop_dc)
    return


if __name__ == '__main__':
    gen_test()
