import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions

import time
import requests
from collections import Counter
import re
import os

# Your translation API setup
url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
headers = {
    "x-rapidapi-key": "27e5dd421emshed3300e6543ac79p1d1807jsn0520497fb758",
    "x-rapidapi-host": "rapid-translate-multi-traduction.p.rapidapi.com",
    "Content-Type": "application/json "
}

@pytest.fixture(scope="function")
def driver():
    """Create and yield a WebDriver instance for each test"""
    options = ChromeOptions()
    options.set_capability('sessionName', 'BStack Sample Test')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def download_image(url, save_folder='images'):
    try:
        # Send a GET request to the image URL
        response = requests.get(url)
        
        # Check if the response is successful (status code 200)
        if response.status_code == 200:
            # Ensure the save folder exists, create it if not
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            
            # Get the image filename from the URL (use the last part of the URL)
            image_name = os.path.join(save_folder, url.split('/')[-1].split('?')[0])

            # Write the image content to a file
            with open(image_name, 'wb') as f:
                f.write(response.content)
            
            print(f"Image saved as {image_name}")
        else:
            print(f"Failed to retrieve the image from {url} (Status code: {response.status_code})")
    
    except Exception as e:
        print(f"An error occurred while downloading the image")

def get_best_image_url(src):
    # Split the src into multiple URLs
    image_sources = src.split(',')
    
    # Sort the URLs based on the width (the number before "w")
    sorted_sources = sorted(image_sources, key=lambda x: int(x.split()[-1][:-1]), reverse=True)
    
    # Return the URL with the largest width
    return sorted_sources[0].split()[0]

def translate_text(text, from_lang="es", to_lang="en"):
    payload = {
        "from": from_lang,
        "to": to_lang,
        "q": text
    }
    response = requests.post(url, json=payload, headers=headers)
    
    # Check if the API call was successful
    if response.status_code == 200:
        translation = response.json()
        return translation[0]
    else:
        print(f"Error: {response.status_code}")
        return None

# Function to tokenize and clean text
def clean_and_tokenize(text):
    # Convert to lowercase and remove non-alphabetical characters
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    return words

def test_elpais_scraping(driver):
    """Test to scrape El Pais website and analyze content"""
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.maximize_window()
        driver.get("https://elpais.com/")
        
        # Wait for page to load
        time.sleep(5)

        # ****************** check if language is spanish
        lang_attr = driver.find_element(By.TAG_NAME, 'html').get_attribute('lang')
        if 'es' in lang_attr:
            print('language is spanish')
        else:
            print(f'language is {lang_attr}')

        # accept something (don't know the spanish language)
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
        accept_button.click()
        
        # go to opinions page
        opinion_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@data-mrf-link="https://elpais.com/opinion/"]')))
        opinion_button.click()

        # wait for page to load
        time.sleep(5)

        # get main element in which articles are present
        opinion_section = wait.until(EC.visibility_of_element_located((By.XPATH, '//section[@data-dtm-region="portada_apertura"]')))
        articles = opinion_section.find_elements(By.TAG_NAME, 'article')  # if less than 5, then add more from somewhere
        articles = articles[:5] if len(articles) > 5 else articles

        tc_dict = {}

        img_scr_list = []

        for article in articles:
            title = article.find_element(By.XPATH, './/h2').text
            content = article.find_element(By.XPATH, './/p').text
            tc_dict[title] = content

            try:
                img_scr = article.find_element(By.TAG_NAME, 'img').get_attribute('srcset')
                if img_scr:
                    img_scr_list.append(get_best_image_url(img_scr))
            except Exception as e:
                # Handle the case where no <img> tag is found within the <article>
                print(f"No image found in this article or error occurred: {title}")

        print(tc_dict)
        print(len(img_scr_list))
        print(f"total number of images: {img_scr_list}")

        # Step 1: Translate titles and store them
        translated_titles = []
        for title, content in tc_dict.items():
            translated_title = translate_text(title)
            if translated_title:
                translated_titles.append(translated_title)
            else:
                print(f"Failed to translate title: {title}")

        print(translated_titles)

        # Step 2: Tokenize and count word occurrences across all translated titles
        all_words = []

        for title in translated_titles:
            words = clean_and_tokenize(title)
            all_words.extend(words)

        # Count word occurrences
        word_counts = Counter(all_words)

        # Identify and print words that appear more than twice
        repeated_words = {word: count for word, count in word_counts.items() if count >= 2}

        print("Repeated words (appearing more than twice):")
        for word, count in repeated_words.items():
            print(f"{word} has occurred {count} times")

        # Download cover image
        for url in img_scr_list:
            download_image(url)

        print("Test completed successfully!")

    except Exception as e:
        print(f"Test failed with error: {e}")
        raise e