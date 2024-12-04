from selenium import webdriver
import pickle
from argparse import ArgumentParser
import sys

def save_cookies(driver, output_path):
    with open(output_path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print(f"Cookies saved to {output_path}")

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
