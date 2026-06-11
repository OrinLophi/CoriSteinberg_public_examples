#  Author: {{AUTHOR}}
#  Creation Date: {{DATE}}
#  Automation for:
#      {{CLIENT}} {{PACKAGE}}

from functions import *
from models import run_data, ErrorCodes
import mail_import as mi

import json
import time
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import ScreenshotException

def launch_session():
    # These are the default caps used in platform
    caps = {"deviceName": "Android",
            "platformName": "Android",
            "appPackage": "{{PACKAGE}}",
            "appActivity": "{{ACTIVITY}}",
            "automationName": "UiAutomator2",
            "noSign": True,
            "noReset": True,
            "dontStopAppOnReset": True,
            "skipDeviceInitialization": True,
            "skipUnlock": True,
            "mockLocationApp": None}

    return webdriver.Remote("http://localhost:4723/wd/hub", caps)

def primary_functionality(driver_object):
    run_data.data_written = "{{mm.dd.yyyy}}"
    local_defaults = ["", ""]
    keys = ["username", "password"]

    # import config data
    data = import_config(driver_object)

    # Username and password will be pulled from the config file in platform
    # This will allow us to dynamically adjust credentials without needing a rescript
    # username & password can we used as variables.
    if data:
        creds = {}
        for k, v in zip(keys, local_defaults):
            creds.update({k: load_creds(k, v, data)})

    else:
        creds = dict(zip(keys, local_defaults))

    # add the total actions expected to the rundata dictionary to record login success enter the element expected as
    # the second argument, ex: success(driver_object, "//android.widget.Button[@text='OK']") or success(
    # driver_object, "com.android.chrome:id/terms_accept")

    {{CODE}}

    success(driver_object, "el_string", "elementSearchType")
    take_screenshot(driver_object)

def main():
    driver = launch_session()
    run_data.error_code = ErrorCodes.FAILED_TO_LAUNCH
    driver.log_event("nowsecure", "Session Launched")
    driver.log_event("nowsecure", "RunData Present in Script")

    try:
        primary_functionality(driver)
    except Exception as err:
        print(f"Workflow exited with {err=}, {type(err)=}")
        driver.log_event("nowsecure", f"Workflow exited with {err=}, {type(err)=}")
        # If the scripts errors after a successful login, then it's a post-login error
        if run_data.error_code is None:
            run_data.error_code = ErrorCodes.POST_LOGIN_WORKFLOW_ERROR

    driver.log_event("nowsecure", f"RunData:{run_data.dumps()}")
    print('appium', f"RunData:{(run_data.dumps())}")
    take_screenshot(driver)
    print("Session Complete")
    driver.quit()


if __name__ == "__main__":
    main()
