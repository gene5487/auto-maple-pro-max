"""A module for detecting and notifying the user of dangerous in-game events."""

from src.common import config, utils
import time
import os
import cv2
import pygame
import threading
import numpy as np
import keyboard as kb
from src.routine.components import Point

###### Line Notify ######
import requests
from datetime import datetime
import pyautogui


def line_notify(msg):
    data = {
        'message': msg
    }
    requests.post(config.url, headers=config.headers, data=data)


def line_screenshot(file_name='./screenshot.png'):
    data = {
        'message': f'{datetime.now().strftime("%H:%M:%S")} 截圖:'
    }
    pyautogui.screenshot().save(file_name)
    image = open(file_name, 'rb')
    files = {'imageFile': image}
    requests.post(config.url, headers=config.headers, data=data, files=files)


# bounty_portals_template image
BOUNTY_PORTALS_TEMPLATE = cv2.imread('assets/bounty_portals_template.png', 0)

# fiona_lie_detector image
FIONA_LIE_DETECTOR_TEMPLATE = cv2.imread('assets/fiona_lie_detector.png', 0)

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(cv2.imread('assets/rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY)

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread('assets/other_template.png'), OTHER_RANGES)
OTHER_TEMPLATE = cv2.cvtColor(other_filtered, cv2.COLOR_BGR2GRAY)

# The Elite Boss's warning sign
ELITE_TEMPLATE = cv2.imread('assets/elite_template.jpg', 0)


def get_alert_path(name):
    return os.path.join(Notifier.ALERTS_DIR, f'{name}.mp3')


class Notifier:
    ALERTS_DIR = os.path.join('assets', 'alerts')

    def __init__(self):
        """Initializes this Notifier object's main thread."""

        pygame.mixer.init()
        self.mixer = pygame.mixer.music

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

        self.room_change_threshold = 0.9
        self.rune_alert_delay = 120

    def start(self):
        """Starts this Notifier's thread."""

        print('\n[~] Started notifier')
        self.thread.start()

    def _main(self):
        self.ready = True
        prev_others = 0
        rune_start_time = time.time()
        while True:
            if config.enabled:
                frame = config.capture.frame
                height, width, _ = frame.shape
                minimap = config.capture.minimap['minimap']

                # Check for unexpected black screen
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if np.count_nonzero(gray < 15) / height / width > self.room_change_threshold:
                    self._alert('siren')
                    line_notify(f'{datetime.now().strftime("%H:%M:%S")} 發現黑畫面')
                    line_screenshot(file_name='./screenshot_black_screen.png')

                # Check for fiona_lie_detector, copied from: https://github.com/sean820117/auto-maple/blob/f97116cf97426b5847e73d3185ca39e3bfc74eda/src/modules/notifier.py#L122
                fiona_frame = frame[height - 400:height, width - 300:width]
                fiona_lie_detector = utils.multi_match(fiona_frame, FIONA_LIE_DETECTOR_TEMPLATE, threshold=0.9)
                if len(fiona_lie_detector) > 0:
                    print("find fiona_lie_detector")
                    line_notify(f'{datetime.now().strftime("%H:%M:%S")} 發現菲歐娜測謊')
                    line_screenshot(file_name='./screenshot_fiona_lie_detector.png')
                    self._alert('siren')
                    time.sleep(0.1)

                # Check for bounty portals
                matches = utils.multi_match(minimap, BOUNTY_PORTALS_TEMPLATE, threshold=0.9)
                if len(matches) > 0:
                    self._ping('MH-Combine Item')
                    line_notify(f'{datetime.now().strftime("%H:%M:%S")} 發現賞金獵人傳送門')
                    line_screenshot(file_name='./screenshot_bounty_portals.png')

                # Check for elite warning
                elite_frame = frame[height // 4:3 * height // 4, width // 4:3 * width // 4]
                elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
                if len(elite) > 0:
                    self._alert('siren')
                    line_notify(f'{datetime.now().strftime("%H:%M:%S")} 發現精英警告')
                    line_screenshot(file_name='./screenshot_elite_warning.png')

                # Check for other players entering the map
                filtered = utils.filter_color(minimap, OTHER_RANGES)
                others = len(utils.multi_match(filtered, OTHER_TEMPLATE, threshold=0.5))
                config.stage_fright = others > 0
                if others != prev_others:
                    if others > prev_others:
                        self._ping('ding')
                    prev_others = others

                # Check for rune
                now = time.time()
                if not config.bot.rune_active:
                    if config.bot.rune_solved:
                        config.bot.rune_solved = False
                        self._ping('MH-Item Found')
                        line_notify(f'{datetime.now().strftime("%H:%M:%S")} 符文已解')
                        line_screenshot(file_name='./screenshot_rune_solved.png')

                    filtered = utils.filter_color(minimap, RUNE_RANGES)
                    matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
                    rune_start_time = now
                    if matches and config.routine.sequence:
                        abs_rune_pos = (matches[0][0], matches[0][1])
                        config.bot.rune_pos = utils.convert_to_relative(abs_rune_pos, minimap)
                        distances = list(map(distance_to_rune, config.routine.sequence))
                        index = np.argmin(distances)
                        config.bot.rune_closest_pos = config.routine[index].location
                        config.bot.rune_active = True
                        self._ping('rune_appeared', volume=0.75)
                        line_notify(f'{datetime.now().strftime("%H:%M:%S")} 發現符文')
                        line_screenshot(file_name='./screenshot_rune_appeared.png')
                elif now - rune_start_time > self.rune_alert_delay:     # Alert if rune hasn't been solved
                    config.bot.rune_active = False
                    self._alert('siren')
                    line_notify(f'{datetime.now().strftime("%H:%M:%S")} 符文未解')
                    line_screenshot(file_name='./screenshot_rune_unsolved.png')
            time.sleep(0.05)

    def _alert(self, name, volume=0.75):
        """
        Plays an alert to notify user of a dangerous event. Stops the alert
        once the key bound to 'Start/stop' is pressed.
        """

        config.enabled = False
        config.listener.enabled = False
        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play(-1)
        while not kb.is_pressed(config.listener.config['Start/stop']):
            time.sleep(0.1)
        self.mixer.stop()
        time.sleep(2)
        config.listener.enabled = True

    def _ping(self, name, volume=0.5):
        """A quick notification for non-dangerous events."""

        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play()


#################################
#       Helper Functions        #
#################################
def distance_to_rune(point):
    """
    Calculates the distance from POINT to the rune.
    :param point:   The position to check.
    :return:        The distance from POINT to the rune, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(config.bot.rune_pos, point.location)
    return float('inf')
