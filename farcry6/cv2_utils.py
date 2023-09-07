import logging
import os
import time
from enum import Enum

import cv2
import imutils
import numpy as np
import pyautogui as gui
import pydirectinput as user

DEFAULT_MATCH_THRESHOLD = 0.8
DEFAULT_INTERVAL = 2  # seconds
DEFAULT_TIMEOUT = 60  # seconds

# path relative to script
script_dir = os.path.dirname(os.path.realpath(__file__))
images_dir = os.path.join(script_dir, "images")
dir16x9 = os.path.join(images_dir, "16x9")
dir16x10 = os.path.join(images_dir, "16x10")

templates = {
    "options": {
        "16x10": cv2.imread(os.path.join(dir16x9, "options_menu_1080.png"), cv2.IMREAD_UNCHANGED),
        "16x9": cv2.imread(os.path.join(dir16x9, "options_menu_1080.png"), cv2.IMREAD_UNCHANGED)
    },
    "benchmark": {
        "16x10": cv2.imread(os.path.join(dir16x9, "benchmark_1080.png"), cv2.IMREAD_UNCHANGED),
        "16x9": cv2.imread(os.path.join(dir16x9, "benchmark_1080.png"), cv2.IMREAD_UNCHANGED)
    },
    "header": {
        "16x10": cv2.imread(os.path.join(dir16x9, "results_header_1080.png"), cv2.IMREAD_UNCHANGED),
        "16x9": cv2.imread(os.path.join(dir16x9, "results_header_1080.png"), cv2.IMREAD_UNCHANGED)
    },
}


def get_template(name, set="16x9"):
    return templates[name][set]


class ClickType(Enum):
    SINGLE = 0  # uses .click()
    DOUBLE = 1  # uses .doubleclick()
    HARD = 2  # uses mouse.down() and mouse.up()


def get_middle_of_rect(top_left_corner, height, width):
    x = top_left_corner[0] + (width / 2)
    y = top_left_corner[1] + (height / 2)
    return int(x), int(y)  # round to avoid fractional pixels


def click(top_left_corner, img):
    click_loc = get_middle_of_rect(top_left_corner, img.shape[0], img.shape[1])
    logging.info(f"Clicking {click_loc}")
    gui.click(click_loc[0], click_loc[1])


def double_click(top_left_corner, img):
    click_loc = get_middle_of_rect(top_left_corner, img.shape[0], img.shape[1])
    logging.info(f"Double clicking {click_loc}")
    user.doubleClick(click_loc[0], click_loc[1])


def hard_click(top_left_corner, img):
    click_loc = get_middle_of_rect(top_left_corner, img.shape[0], img.shape[1])
    print(f"Hard click loc {click_loc}")
    user.moveTo(click_loc[0], click_loc[1])
    user.mouseDown()
    user.mouseUp()


def wait_and_click(template_name, name, click_type: ClickType = ClickType.SINGLE, timeout=DEFAULT_TIMEOUT):
    logging.info(f"Waiting to find and click on {name}")
    img, img_loc = wait_for_image_on_screen(template_name, timeout=timeout)
    print(f"Wait and click: {img_loc}")
    if click_type == ClickType.SINGLE:
        click(img_loc, img)
    elif click_type == ClickType.DOUBLE:
        double_click(img_loc, img)
    elif click_type == ClickType.HARD:
        hard_click(img_loc, img)
    else:
        raise ValueError("Unknown click type")


class ImageNotFoundTimeout(Exception):
    pass


class ImageNotFound(Exception):
    pass


def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)


def aspect_ratio(w, h):
    denom = int(gcd(w, h))
    x = int(w / denom)
    y = int(h / denom)
    if x == 8 and y == 5:
        return "16x10"
    elif x == 16 and y == 9:
        return "16x9"


def locate_on_screen(template_name, threshold=DEFAULT_MATCH_THRESHOLD, debug=1):
    screen = gui.screenshot()
    screen = np.array(
        screen)  # pyautogui is using Pillow which is giving a format that must be adapted to work with opencv.
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    (h, w) = screen.shape[:2]
    r = aspect_ratio(w, h)
    needle = get_template(template_name, r)
    return needle, locate_in_image(needle, screen, threshold=DEFAULT_MATCH_THRESHOLD, debug=0)


# This approach was largely inspired by the article
# https://pyimagesearch.com/2015/01/26/multi-scale-template-matching-using-python-opencv/
def locate_in_image(needle, haystack, threshold=DEFAULT_MATCH_THRESHOLD, debug=0):
    (tH, tW) = needle.shape[:2]

    if debug:
        cv2.imshow("Looking For", needle)
        cv2.waitKey(0)

    for scale in np.linspace(0.2, 1.0, 20)[::-1]:
        # resize the image according to the scale, and keep track
        # of the ratio of the resizing
        resized = imutils.resize(haystack, width=int(haystack.shape[1] * scale), inter=cv2.INTER_NEAREST)
        r = haystack.shape[1] / float(resized.shape[1])

        # if the resized image is smaller than the template, then break
        # from the loop
        if resized.shape[0] < tH or resized.shape[1] < tW:
            break

        result = cv2.matchTemplate(resized, needle, cv2.TM_CCOEFF_NORMED)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

        if debug:
            # draw a bounding box around the detected region
            # clone = np.dstack([edged, edged, edged])
            cv2.rectangle(resized, (maxLoc[0], maxLoc[1]),
                          (maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
            cv2.imshow("Searching", resized)
            cv2.waitKey(0)

        if maxVal >= threshold:
            found = (maxVal, maxLoc, r)

            # unpack the bookkeeping variable and compute the (x, y) coordinates
            # of the bounding box based on the resized ratio
            (_, maxLoc, r) = found
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

            # if debug:
            # draw a bounding box around the detected result and display the image
            cv2.rectangle(haystack, (startX, startY), (endX, endY), (0, 0, 255), 2)
            # cv2.imshow("Found", haystack)

            print(f"x: {startX} y: {startY}")
            cv2.imwrite("found.png", haystack)
            
            # cv2.waitKey(0)

            return startX, startY
    raise ImageNotFound("Image not found on screen")


def wait_for_image_on_screen(template_name, match_threshold=DEFAULT_MATCH_THRESHOLD, interval=DEFAULT_INTERVAL,
                             timeout=DEFAULT_TIMEOUT):
    """Function that will wait for an image to appear on screen. This function will check every
     interval for a match that meets is greater than the match threshold. The function will raise
     an error if the image is not found within the timeout given. Will return the location
     of the image if found"""
    t0 = time.time()
    t1 = t0
    while not t1 - t0 > timeout:
        try:
            img, loc = locate_on_screen(template_name, match_threshold)
            return img, loc
        except ImageNotFound:
            pass
        time.sleep(interval)
        t1 = time.time()
    raise ImageNotFoundTimeout("Could not find image on screen within timeout")
