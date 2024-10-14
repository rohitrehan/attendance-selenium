import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WAIT_DELAY = 50  # seconds


def get_browser() -> webdriver.Firefox:
    driver_path = os.path.join(CURRENT_DIR, "..", "drivers", "geckodriver.exe")
    service = Service(executable_path=driver_path)
    options = webdriver.FirefoxOptions()
    options.binary_location = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    return webdriver.Firefox(service=service, options=options)


def get_config():
    config = {}
    with open(os.path.join(CURRENT_DIR, "..", "config", "config"), 'r') as f:
        for line in f:
            tokens = line.split("=")
            config[tokens[0]] = tokens[1].strip()
    return config


def verify_wait_me(browser):
    try:
        time.sleep(3)
        WebDriverWait(browser, WAIT_DELAY).until(
            EC.invisibility_of_element((By.CLASS_NAME, "waitMe")))
        time.sleep(2)
    except TimeoutException:
        raise ("Loading took too much time!")


def wait_for_element_by_id(browser, selector, wait_delay=WAIT_DELAY):
    try:
        WebDriverWait(browser, wait_delay).until(
            EC.presence_of_element_located((By.ID, selector)))
    except TimeoutException:
        raise ("Loading took too much time!")


def wait_for_element_by_xpath(browser, selector, wait_delay=WAIT_DELAY):
    try:
        WebDriverWait(browser, wait_delay).until(
            EC.presence_of_element_located((By.XPATH, selector)))
    except TimeoutException:
        raise ("Loading took too much time!")


def login(browser, config):
    url = f'{config["url"]}/iApp/MVC/Login'
    browser.get(url)
    browser.maximize_window()

    # long wait in case of VPN/organization security
    wait_for_element_by_id(browser, 'txtUserName', WAIT_DELAY*5)

    element = browser.find_element(By.ID, "txtUserName")
    element.send_keys(config["username"])

    element = browser.find_element(By.ID, "txtPassword")
    element.send_keys(config["password"])

    element = browser.find_element(By.ID, "btnLogin")
    element.click()

    wait_for_element_by_id(browser, 'User')


def apply(browser, date, config):
    print(f"Applying attendance for: {date}")
    url = f"{config['url']}/iApp/MVC/OutDoorDuty/Index?MenuId=69&CallFrom=PortalSheet&isPopup=Y&trans=ADDOD&id=811,{date},0,,0,0.00,0.00,0.00,,"
    browser.get(url)

    verify_wait_me(browser)
    wait_for_element_by_id(browser, "ButtonSave")

    time.sleep(5)

    browser.find_element(By.ID, "s2id_ShiftCombo").click()
    browser.find_element(
        By.XPATH, f'//li/div[contains(.,\'{config["shift"]}\')]').click()

    browser.find_element(By.ID, "item_chkOutdoorduty").click()
    verify_wait_me(browser)

    browser.find_element(By.ID, "0Fromtime").send_keys(config['start_time'])
    browser.find_element(By.ID, "0Totime").send_keys(config['end_time'])

    verify_wait_me(browser)

    browser.find_element(By.ID, "s2id_0RG").click()
    browser.find_element(By.XPATH, "//li/div[contains(.,'General')]").click()
    browser.find_element(By.ID, "0reason").send_keys(config['duty_reason'])
    browser.find_element(By.ID, "ButtonSave").click()
    time.sleep(10)


def main():
    config = get_config()
    browser = get_browser()

    login(browser, config)

    browser.get(f"{config['url']}/iApp/MVC/Portal?MenuID=62")

    wait_for_element_by_xpath(
        browser, "//td[@role='gridcell'][@aria-describedby='portalgrid_Status']")

    time.sleep(5)

    elements = browser.find_elements(
        By.XPATH, "//td[@role='gridcell'][@aria-describedby='portalgrid_Status'][@style='color: rgb(255, 0, 0);']")

    dates = []
    for ele in elements:
        parent = ele.find_element(By.XPATH, "..")
        ele = parent.find_element(
            By.XPATH, "td[@aria-describedby='portalgrid_Out Door Duty']")
        if (ele.get_attribute('style') == 'background-color: rgb(0, 0, 255);'):
            continue
        
        leave_ele = parent.find_element(
            By.XPATH, "td[@aria-describedby='portalgrid_Leave']")
        if (leave_ele.get_attribute('style') == 'background-color: rgb(0, 0, 255);'):
            continue

        date = parent.text.split()[0].strip()
        dates.append(date)

    print(f"Applying attendance for {len(dates)} days")
    for date in dates:
        apply(browser, date, config)
        time.sleep(10)

    time.sleep(10)

    print("clicked")
    browser.quit()


if __name__ == '__main__':
    exit(main())
