from selenium import webdriver
import pickle
from argparse import ArgumentParser
import sys
import time


def save_cookies(driver, output_path: str):
    """
    Save cookies from the Selenium WebDriver to a file.

    Args:
        driver: Selenium WebDriver instance.
        output_path (str) : Path to save the cookies file.
    """
    cookies = driver.get_cookies()
    with open(output_path, "wb") as file:
        pickle.dump(cookies, file)
    print(f"Cookies saved to {output_path}.")

def main(url, output_path):
    """
    Main function to open a URL in a web browser and save cookies.

    Arguments:
        url (str) : URL to open in the web browser.
        output_path (str) : Directory to store output folders.
    """
    print(f"Opening {url}. Please log in manually.")
    driver = webdriver.Chrome()
    driver.get(url)
    input("Log in and press Enter when done...")
    save_cookies(driver, output_path)
    driver.quit()

def parse_args(arglist):
    """Parse command line arguments.

    Arguments:
        arglist (list): List of command line arguments.
    Returns:
        Namespace: Parsed arguments.
    """
    parser = ArgumentParser()
    parser.add_argument("--url", "-u", required=True, help="Url")
    parser.add_argument("--output_path", "-o", required=True, help="Output Path")
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.url, args.output_path)
