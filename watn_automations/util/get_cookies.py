from selenium import webdriver
import pickle
from argparse import ArgumentParser
import sys
import time

def extend_cookie_expiry(cookies, years=10):
    far_future = int(time.time()) + years * 365 * 24 * 60 * 60 
    for cookie in cookies:
        cookie['expiry'] = far_future
    return cookies

def save_cookies(driver, output_path):
    cookies = driver.get_cookies()
    cookies = extend_cookie_expiry(cookies)
    with open(output_path, "wb") as file:
        pickle.dump(cookies, file)
    print(f"Cookies saved to {output_path} with extended expiry")

def main(url, output_path):
    # Step 1: Save cookies after manual login
    print(f"Opening {url}. Please log in manually.")
    driver = webdriver.Chrome()
    driver.get(url)
    input("Log in and press Enter when done...")
    save_cookies(driver, output_path)
    driver.quit()

def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--url", "-u", required=True, help="Url")
    parser.add_argument("--output_path", "-o", required=True, help="Output Path")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.url, args.output_path)
