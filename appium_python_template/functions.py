import json
import time
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import ScreenshotException
from models import run_data, ErrorCodes


# this function use the element coordinate to tap the element
# use case: forceTapElem(driver, wait_for(driver_object, "//android.widget.TextView[@text='OK']", "xpath", 1)
# or
# elem = wait_for(driver_object, "//android.widget.TextView[@text='OK']", "xpath", 1)
# forceTapElem(driver,elem)

def force_tap_elem(driver_object, element):

    # Get the element's bounds attribute
    bounds = element.get_attribute('bounds')

    # Extract the coordinates by splitting the bounds string
    x1, y1, x2, y2 = map(int, bounds.replace('][', ',').replace('[', '').replace(']', '').split(','))

    # Calculate the center of the element
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    # Tap at the center of the element using TouchAction
    TouchAction(driver_object).tap(x=center_x, y=center_y).perform()


# scroll function
def scroll(driver_object, from_x, from_y, to_x, to_y):
    driver_object.swipe(from_x, from_y, to_x, to_y)


# Scroll to Bottom of the page
def scroll_down_big(driver_object):
    scroll_to_bottom = 'new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollToEnd(5);'
    try:
        driver_object.find_element_by_android_uiautomator(scroll_to_bottom)
    except Exception as e:
        print(f"Scroll attempt failed with error: {e}, type: {type(e)}")
        driver_object.log_event("nowsecure", f"Scroll attempt failed with error: {e}, type: {type(e)}")


# get rid of android permissions
def permission(driver_object, timeout_max=0, sleep_interval=1):
    # If the permission container doesn't exist, exit early
    if timeout_max > 0 and not wait_exist(driver_object, 'com.android.permissioncontroller:id/content_container', 'id', timeout_max):
        return

    permission_list = [
        ("//android.widget.Button[@text='Allow']", "xpath"),
        ("com.android.permissioncontroller:id/permission_allow_one_time_button", "id"),
        ("com.android.permissioncontroller:id/permission_allow_button", "id"),
        ("com.android.permissioncontroller:id/permission_allow_foreground_only_button", "id"),
        ("//android.widget.Button[@text='Allow Once']", "xpath"),
        ("//android.widget.Button[@text='Always Allow']", "xpath"),
        ("//android.widget.Button[@text='OK']", "xpath")
    ]
    # Loop through permissions, with no sleeps in between
    for el_string, path_type in permission_list:
        if tap_if_exists(driver_object, el_string, path_type, timeout_max, sleep_interval):
            return


# Clear chrome first run screens
def handle_chrome(driver_object):
    tap_if_exists(driver_object, "com.android.chrome:id/signin_fre_dismiss_button", "id")
    if tap_if_exists(driver_object, 'com.android.chrome:id/terms_accept', 'id', 5):
        tap_if_exists(driver_object, 'com.android.chrome:id/negative_button', 'id', 5)
    tap_if_exists(driver_object, '//*[@text="Got it"]', 'xpath', 5)


def wait_for(driver_object, el_string, path_type, timeout_max=30, sleep_interval=1):
    take_screenshot(driver_object)
    print("Searching for " + el_string + " by " + path_type)
    timeout_variable = 0
    while timeout_variable < timeout_max:
        elx = []

        if path_type == 'id':
            elx = driver_object.find_elements_by_id(el_string)
        elif path_type == 'xpath':
            elx = driver_object.find_elements_by_xpath(el_string)
        elif path_type == 'accessibility_id':
            elx = driver_object.find_elements_by_accessibility_id(el_string)
        else:
            raise Exception("path_type Not Supported")

        if len(elx) > 0:
            if run_data.error_code is None:
                run_data.error_code = ErrorCodes.WORKFLOW_ERROR
            return elx

        else:
            print("waiting...")

        timeout_variable += 1
        time.sleep(sleep_interval)

    raise Exception("Element not present")


def wait_exist(driver_object, el_string, path_type, timeout_max=30, sleep_interval=1):
    take_screenshot(driver_object)
    print("Searching for " + el_string + " by " + path_type)
    timeout_variable = 0
    while timeout_variable < timeout_max:
        try:
            if path_type == 'id':
                driver_object.find_element_by_id(el_string)
                return True
            elif path_type == 'xpath':
                driver_object.find_element_by_xpath(el_string)
                return True
            elif path_type == 'accessibility_id':
                driver_object.find_element_by_accessibility_id(el_string)
                return True
            else:
                raise Exception("path_type Not Supported")

        except:
            print("waiting...")

        timeout_variable += 1
        time.sleep(sleep_interval)
    return False


def tap_if_exists(driver_object, el_string, path_type, timeout_max=30, sleep_interval=1):
    if wait_exist(driver_object, el_string, path_type, timeout_max, sleep_interval):
        wait_for(driver_object, el_string, path_type, 5)[0].click()
        return True
    return False


def take_screenshot(driver_object):
    try:
        driver_object.get_screenshot_as_base64()
    except ScreenshotException:
        print("Could not take screenshot; FLAG_SECURE enabled")
        driver_object.log_event("nowsecure", "Could not take screenshot; FLAG_SECURE enabled")


def login_success_fallback(driver_object):
    take_screenshot(driver_object)
    driver_object.log_event('nowsecure', 'Attempting login success fallback function')
    print('Attempting login success fallback function')

    # Get snapshot of the current element tree
    import xml.etree.ElementTree as ET
    xml_tree = ET.fromstring(driver_object.page_source)

    # However, if login failure message is a popup, it will sometimes hide the password field from the element tree
    # So we check all the elements' text and accessibility id fields and look for various keywords
    element_strings = {*(t.attrib.get('text', '') for t in xml_tree.iter()),
                       *(t.attrib.get('content-desc', '') for t in xml_tree.iter())}
    negative_keywords = ['error', 'failed', 'try again', 'incorrect', 'invalid', 'please enter a valid']
    for s in element_strings:
        for keyword in negative_keywords:
            if keyword in s.lower():
                driver_object.log_event('nowsecure', f'Login failed - Found keyword "{keyword}" in string {repr(s)}')
                print(f'Login failed - Found keyword "{keyword}" in string {repr(s)}')
                return False

    # Do the same thing to check if we're on the home screen
    positive_keywords = ['home', 'profile', 'settings', 'log out', 'sign out']
    for s in element_strings:
        for keyword in positive_keywords:
            if keyword in s.lower():
                driver_object.log_event('nowsecure', f'Login succeeded - Found keyword "{keyword}" in string {repr(s)}')
                print(f'Login succeeded - Found keyword "{keyword}" in string {repr(s)}')
                return True

    # On successful login, the password field should always disappear
    # TODO: A few apps don't use the password="true" attribute for their password fields
    #  In this case, it could potentially look for 2+ text fields instead, but that may cause some false negatives
    if xml_tree.find('.//android.widget.EditText[@password="true"]') is not None:
        driver_object.log_event('nowsecure', 'Login failed - Password field still exists')
        print('Login failed - Password field still exists')
        return False

    # Return False by default
    driver_object.log_event('nowsecure', 'Login inconclusive - No indicators of success/failure found')
    print('Login inconclusive - No indicators of success/failure found')
    run_data.error_code = ErrorCodes.LOGIN_UNKNOWN
    return False

# record login success
def success(driver_object, el_string, path_type, timeout_max=30, use_fallback=True):
    run_data.error_code = ErrorCodes.SUBMISSION_FAILURE
    if wait_exist(driver_object, el_string, path_type, timeout_max):
        run_data.login_success = True
    elif use_fallback:
        run_data.login_success = login_success_fallback(driver_object)
    if run_data.login_success:
        run_data.error_code = None
    take_screenshot(driver_object)


# import configuration data file which will be copied automatically to the appium folder in platform
def import_config(driver_object):
    try:
        f = open('config.json')
        # returns JSON object as a dictionary
        return json.load(f)
    except Exception as import_config_err:
        print("Failed to open json file, using defaults in script")
        print(f"Unexpected {import_config_err=}, {type(import_config_err)=}")
        driver_object.log_event("nowsecure", "Failed to open json file, using defaults in script")
        driver_object.log_event("nowsecure", f"Unexpected {import_config_err=}, {type(import_config_err)=}")
        return None


def load_creds(key, passed_default, data):
    if 'search_data' in data and key in data['search_data']:
        passed_default = data['search_data'][key]['value']
        # print("Value in first loop = " + passed_default)
    elif 'search_terms' in data:
        for d in data['search_terms']:
            if d['name'] == key:
                passed_default = d['value']
                # print("Value in 2nd loop = " + passed_default)
    elif 'search_data' in data:
        for search_term in data['search_data'].values():
            if 'type' in search_term and search_term['type'] == key:
                passed_default = search_term['value']
                # print("Value in 3rd loop = " + passed_default)

    # print("Value in final value = " + passed_default)
    return passed_default
