from argparse import ArgumentParser
import logging
import os.path
import time
import pydirectinput as user
from subprocess import Popen
import sys


from f1_23_utils import get_resolution, remove_intro_videos, skippable

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from harness_utils.logging import *
from harness_utils.process import terminate_processes
from harness_utils.keras_service import KerasService
from harness_utils.steam import DEFAULT_EXECUTABLE_PATH as STEAM_PATH

SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
LOG_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "run")
STEAM_GAME_ID = 2108330
STEAM_PATH = os.path.join(os.environ["ProgramFiles(x86)"], "steam")
STEAM_EXECUTABLE = "steam.exe"
PROCESS_NAME = "F1_23"


def is_word_on_screen(word: str, attempts: int = 5, delay_seconds: int = 1) -> bool:
    for _ in range(attempts):
        result = kerasService.capture_screenshot_find_word(word)
        if result != None:
            return True
        time.sleep(delay_seconds)
    return False


def start_game():
    steam_run_arg = "steam://rungameid/" + str(STEAM_GAME_ID)
    start_cmd = STEAM_PATH + "\\" + STEAM_EXECUTABLE
    logging.info(start_cmd + " " + steam_run_arg)
    thread =  Popen([start_cmd, steam_run_arg])
    return thread

def official() -> any:
    return is_word_on_screen(word="product", attempts=20, delay_seconds=0.5)
    
def press() -> any:
    return is_word_on_screen(word="press", attempts=40, delay_seconds=2)

def login() -> any:
    return is_word_on_screen(word="login", attempts=100, delay_seconds=0.2)

def benchmark_start() -> any:
    return is_word_on_screen(word="lap", attempts=15, delay_seconds=3)

def results() -> any:
    return is_word_on_screen(word="results", attempts=20, delay_seconds=3)

def menu() -> any:
    return is_word_on_screen(word="theatre", attempts=5, delay_seconds=3)

def settings() -> any:
    return is_word_on_screen(word="settings", attempts=5, delay_seconds=3)

def graphics() -> any:
    return is_word_on_screen(word="graphics", attempts=5, delay_seconds=3)

def benchmark() -> any:
    return is_word_on_screen(word="benchmark", attempts=5, delay_seconds=3)

def weather() -> any:
    return is_word_on_screen(word="weather", attempts=5, delay_seconds=3)


# ASSUMPTIONS
# 1. We are doing 3 laps
def run_benchmark():
    remove_intro_videos(skippable)
    start_game()
    t1 = time.time()

    time.sleep(2)

    # press space through the warnings
    start_game_screen= time.time()
    while (True):
        if official():
            logging.info('Game started. Skipping intros.')
            user.press("space")
            time.sleep(1)
            user.press("space")
            time.sleep(1)
            user.press("space")
            time.sleep(4)
            break
        elif time.time()-start_game_screen>60:
            logging.info("Game didn't start in time. Check settings and try again.")
            exit(1)
        logging.info("Game hasn't started. Trying again in 5 seconds")
        time.sleep(5)
    
    # Press enter to proceed to the main menu
    start_game_screen= time.time()
    while (True):
        if press():
            logging.info('Hit the title screen. Continuing')
            user.press("enter")
            time.sleep(1)
            break
        elif time.time()-start_game_screen>60:
            logging.info("Game didn't start in time. Check settings and try again.")
            exit(1)
        logging.info("Game hasn't started. Trying again in 5 seconds")
        time.sleep(5)

    # cancel logging into ea services
    if login():   
        logging.info('Cancelling logging in.')
        user.press("enter")
        time.sleep(2)

    ###
    # SHOULD BE ON MAIN MENU RIGHT NOW
    ###
    menu_screen = time.time()
    while (True):
        if menu():
            logging.info('Saw the options! we are good to go!')
            time.sleep(1)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("down")
            time.sleep(0.5)
            user.press("enter")
            time.sleep(2)
            break
        elif time.time()-menu_screen>60:
            logging.info("Didn't land on the main menu!")
            exit(1)
        logging.info("Game still loading. Trying again in 10 seconds")
        time.sleep(10)

    # Enter settings
    if settings():
        user.press("enter")
        time.sleep(1.5)

    # Enter graphics settings
    if graphics():
        user.press("right")
        time.sleep(0.5)
        user.press("enter")
        time.sleep(1.5)

    # Enter benchmark options
    if benchmark():
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("enter")
        time.sleep(1.5)

    # Run benchmark!
    if weather():
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("down")
        time.sleep(0.5)
        user.press("enter")
        time.sleep(2)

    loading_screen_start= time.time()
    while (True):
        if benchmark_start():
            start_time = time.time()
            logging.info("Benchmark started. Waiting for benchmark to complete.")
            break
        elif time.time()-loading_screen_start>60:
            logging.info("Benchmark didn't start.")
            exit(1)
        logging.info("Benchmark hasn't started. Trying again in 10 seconds")
        time.sleep(10)

    t2 = time.time()
    logging.info(f"Setup took {round((t2 - t1), 2)} seconds")

    # sleep for 3 laps
    time.sleep(350)

    results_screen_start= time.time()
    while (True):
        if results():
            logging.info("Results screen was found! Finishing benchmark.")
            break
        elif time.time()-results_screen_start>60:
            logging.info("Results screen was not found! Did harness not wait long enough? Or test was too long?")
            exit(1)
        logging.info("Benchmark hasn't finished. Trying again in 10 seconds")
        time.sleep(10)

    end_time = time.time()
    logging.info(f"Benchmark took {round((end_time - start_time), 2)} seconds")

    """
    Exit
    """
    terminate_processes(PROCESS_NAME)
    return start_time, end_time


setup_log_directory(LOG_DIRECTORY)

logging.basicConfig(filename=f'{LOG_DIRECTORY}/harness.log',
                    format=DEFAULT_LOGGING_FORMAT,
                    datefmt=DEFAULT_DATE_FORMAT,
                    level=logging.DEBUG)
console = logging.StreamHandler()
formatter = logging.Formatter(DEFAULT_LOGGING_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

parser = ArgumentParser()
parser.add_argument("--kerasHost", dest="keras_host", help="Host for Keras OCR service", required=True)
parser.add_argument("--kerasPort", dest="keras_port", help="Port for Keras OCR service", required=True)
args = parser.parse_args()
kerasService = KerasService(args.keras_host, args.keras_port, os.path.join(
    LOG_DIRECTORY, "screenshot.jpg"))

try:
    start_time, end_time = run_benchmark()
    width, height = get_resolution()
    result = {
        "resolution": format_resolution(width, height),
        "graphics_preset": 'current',
        "start_time": seconds_to_milliseconds(start_time),
        "end_time": seconds_to_milliseconds(end_time)
    }

    write_report_json(LOG_DIRECTORY, "report.json", result)
except Exception as e:
    logging.error("Something went wrong running the benchmark!")
    logging.exception(e)
    terminate_processes(PROCESS_NAME)
    exit(1)
