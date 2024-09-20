import os
import csv
import difflib
import hashlib
from collections import defaultdict
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from nltk import sent_tokenize

# Function to get multiple URLs via a popup with a multi-line text box
def get_urls_from_popup():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    # Create a new top-level window for multi-line input
    url_input_window = tk.Toplevel(root)
    url_input_window.title("Enter URLs")

    # Create a label
    label = tk.Label(url_input_window, text="Enter URLs (one per line):")
    label.pack()

    # Create a text box for multi-line input
    text_box = tk.Text(url_input_window, height=10, width=50)
    text_box.pack()

    # Variable to store the URLs
    urls = []

    # Create a submit button
    def submit_urls():
        nonlocal urls  # Allows modifying the 'urls' variable in the outer scope
        urls_text = text_box.get("1.0", tk.END)  # Get the text from the text box
        urls = [url.strip() for url in urls_text.splitlines() if url.strip()]  # Process the text into a list of URLs
        url_input_window.quit()  # Close the window after submission
        url_input_window.destroy()  # Destroy the window

    # Create the submit button
    submit_button = tk.Button(url_input_window, text="Submit", command=submit_urls)
    submit_button.pack()

    # Wait for the user to submit the URLs
    root.mainloop()

    # Return the captured URLs after the window is closed
    return urls

# Function to get the user's downloads folder
def get_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")

# Function to write the results to a CSV file
def write_to_csv(data, file_path, headers):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in data:
            writer.writerow(row)

# Function to process each URL and extract content, sentence by sentence
def process_url(url, driver):
    driver.get(url)
    time.sleep(2)  # Allow time for the page to fully load

    # Extract HTML content with BeautifulSoup, limited to <main> tag
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find('main')  # Only search within the <main> tag

    if main_content:
        content = []
        # Extract desired content from elements within <main>
        for tag in ['h1', 'h2', 'p', 'span', 'ul', 'li']:
            elements = main_content.find_all(tag)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text:  # Only append non-empty text
                    # Split the text into sentences using nltk's sent_tokenize
                    sentences = sent_tokenize(text)
                    content.extend(sentences)
        return content
    else:
        return []

# Function to initialize Selenium WebDriver
def initialize_webdriver():
    chrome_path = r"C:\Users\tpsuc\Downloads\Chrome Backup (Duplicate Content Checker)\chrome-win64\chrome.exe"
    driver_path = r"C:\Users\tpsuc\Downloads\Duplicate Content Checker\chromedriver.exe"

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=driver_path)
    return webdriver.Chrome(service=service, options=options)

# Function to compare content between two URLs, sentence-by-sentence
def compare_content(url1, content1, url2, content2):
    local_matches = defaultdict(list)
    if url1 != url2:  # Don't compare the same URL with itself
        hashed_content1 = {hash_content(sentence): sentence for sentence in content1}
        hashed_content2 = {hash_content(sentence): sentence for sentence in content2}

        # Only compare if hash matches
        for hash1, sentence1 in hashed_content1.items():
            if hash1 in hashed_content2:  # Hash matches, compare
                sentence2 = hashed_content2[hash1]
                if are_similar(sentence1, sentence2):  # Perform full difflib comparison
                    local_matches[sentence1].append(url2)
    return url1, local_matches

# Hashing function to quickly compare content
def hash_content(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()

# Function to determine similarity between two texts
def are_similar(text1, text2):
    return difflib.SequenceMatcher(None, text1, text2).ratio() > 0.9

# Function to capture full-page screenshot
def capture_full_page_screenshot(driver, screenshot_path):
    """Capture a full-page screenshot"""
    # Get the original window size
    original_size = driver.get_window_size()

    # Get the total page height using JavaScript
    total_height = driver.execute_script("return document.body.parentNode.scrollHeight")

    # Set the window size to the page's total height
    driver.set_window_size(1920, total_height)

    # Take the screenshot
    driver.save_screenshot(screenshot_path)

    # Reset the window size to its original size
    driver.set_window_size(original_size['width'], original_size['height'])

    print(f"Full-page screenshot saved to {screenshot_path}")

# Function to highlight matching elements on a page
def highlight_elements(driver, elements_to_highlight):
    """Injects CSS into the page to highlight certain elements"""
    for sentence in elements_to_highlight:
        # Escape the text for JavaScript
        escaped_sentence = escape_js_string(sentence)

        # Create a JavaScript snippet to replace the matching sentence with a highlighted version
        script = f"""
        var tags = document.querySelectorAll('h1, h2, p, span, ul, li');
        for (var i = 0; i < tags.length; i++) {{
            var innerText = tags[i].innerText;
            if (innerText.includes("{escaped_sentence}")) {{
                var newHTML = innerText.replace("{escaped_sentence}", "<span style='background-color: yellow;'>{escaped_sentence}</span>");
                tags[i].innerHTML = newHTML;
            }}
        }}
        """
        driver.execute_script(script)

def escape_js_string(text):
    """Escapes special characters for JavaScript strings"""
    return re.sub(r"([\"'\\])", r"\\\1", text)

# Function to track progress
def track_progress(current, total, step_description):
    progress = (current / total) * 100
    print(f"[{datetime.datetime.now()}] {step_description}: {current}/{total} completed ({progress:.2f}% done)")

# Main function to run the program
def main():
    # Get URLs using the popup window before multiprocessing begins
    urls = get_urls_from_popup()

    # Initialize WebDriver for URL content extraction
    driver = initialize_webdriver()

    # Extract content for each URL
    content_per_url = {}
    total_urls = len(urls)
    for index, url in enumerate(urls, start=1):
        print(f"[{datetime.datetime.now()}] Processing: {url}")
        content = process_url(url, driver)
        content_per_url[url] = content
        track_progress(index, total_urls, "URL Processing")

    # Close the WebDriver after content extraction
    driver.quit()

    # Parallelize content comparison using ProcessPoolExecutor
    print(f"[{datetime.datetime.now()}] Starting content comparison phase...\n")
    matches = defaultdict(list)  # Store matches by element
    page_matches = defaultdict(lambda: defaultdict(list))  # Store matches for each page

    with ProcessPoolExecutor(max_workers=5) as executor:
        future_to_compare = {
            executor.submit(compare_content, url1, content1, url2, content2)
            for url1, content1 in content_per_url.items()
            for url2, content2 in content_per_url.items()
        }

        for index1, future in enumerate(as_completed(future_to_compare), start=1):
            url1, local_matches = future.result()
            for elem1, urls in local_matches.items():
                matches[elem1].extend(urls)
                page_matches[url1][elem1].extend(urls)
            track_progress(index1, len(future_to_compare), "Content Comparison")

    # Output CSV: "phrases" CSV (global matches)
    phrases_csv_path = os.path.join(get_downloads_folder(), "phrases.csv")
    write_to_csv([[element, ", ".join(set(duplicate_urls))] for element, duplicate_urls in matches.items()],
                 phrases_csv_path, ["Matching Element", "Duplicate URLs"])
    print(f"[{datetime.datetime.now()}] Data has been saved to {phrases_csv_path}")

    # Output CSV: "page_matches" CSV (individual page matches)
    page_matches_csv_path = os.path.join(get_downloads_folder(), "page_matches.csv")
    page_matches_data = []
    for url, elements in page_matches.items():
        for element, duplicate_urls in elements.items():
            page_matches_data.append([url, element, ", ".join(set(duplicate_urls))])
    write_to_csv(page_matches_data, page_matches_csv_path, ["URL", "Matching Element", "Duplicate URLs"])
    print(f"[{datetime.datetime.now()}] Data has been saved to {page_matches_csv_path}")

    # Reinitialize WebDriver for screenshots
    driver = initialize_webdriver()

    # Screenshot capture with highlighting offending content
    for url, elements in page_matches.items():
        driver.get(url)
        time.sleep(2)  # Wait for the page to fully load

        # Highlight the offending elements
        highlight_elements(driver, elements.keys())

        # Save full-page screenshot
        screenshot_path = os.path.join(get_downloads_folder(), f"screenshot_{url.replace('https://', '').replace('/', '_')}.png")
        capture_full_page_screenshot(driver, screenshot_path)

    # Close the browser after capturing screenshots
    driver.quit()
    print(f"[{datetime.datetime.now()}] Processing complete. Screenshots captured.")

if __name__ == "__main__":
    main()
