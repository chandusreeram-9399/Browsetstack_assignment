from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import requests
from collections import Counter
import re
import os

# Setup Translation API
url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
headers = {
    "x-rapidapi-key": "27e5dd421emshed3300e6543ac79p1d1807jsn0520497fb758",  # Replace with your real key
    "x-rapidapi-host": "rapid-translate-multi-traduction.p.rapidapi.com",
    "Content-Type": "application/json"
}

# Selenium Options
options = Options()
options.add_argument("--start-maximized")

# Auto-manage chromedriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

# Utility functions
def download_image(url, save_folder='images'):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            image_name = os.path.join(save_folder, url.split('/')[-1].split('?')[0])
            with open(image_name, 'wb') as f:
                f.write(response.content)
            print(f"Image saved as {image_name}")
        else:
            print(f"Failed to retrieve image: {url}")
    except Exception as e:
        print(f"Error downloading image: {e}")

def get_best_image_url(src):
    image_sources = src.split(',')
    sorted_sources = sorted(image_sources, key=lambda x: int(x.split()[-1][:-1]), reverse=True)
    return sorted_sources[0].split()[0]

def translate_text(text, from_lang="es", to_lang="en"):
    payload = {"from": from_lang, "to": to_lang, "q": text}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()[0]
    else:
        print(f"Translation error ({response.status_code}): {text}")
        return None

def clean_and_tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text.split()

# Main automation
try:
    driver.get("https://elpais.com/")
    time.sleep(5)

    lang = driver.find_element(By.TAG_NAME, 'html').get_attribute('lang')
    print("Language detected:", lang)

    # Accept cookies
    accept_btn = wait.until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
    accept_btn.click()

    # Go to Opinion section
    opinion_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@data-mrf-link="https://elpais.com/opinion/"]')))
    opinion_btn.click()
    time.sleep(5)

    opinion_section = wait.until(EC.visibility_of_element_located((By.XPATH, '//section[@data-dtm-region="portada_apertura"]')))
    articles = opinion_section.find_elements(By.TAG_NAME, 'article')
    articles = articles[:5] if len(articles) >= 5 else articles

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
        except:
            print(f"No image found for article: {title}")

    print("Articles:", tc_dict.keys())

    translated_titles = []
    for title in tc_dict.keys():
        translated = translate_text(title)
        if translated:
            translated_titles.append(translated)

    all_words = []
    for title in translated_titles:
        words = clean_and_tokenize(title)
        all_words.extend(words)

    word_counts = Counter(all_words)
    repeated_words = {word: count for word, count in word_counts.items() if count >= 2}

    print("\nRepeated Words (≥2 times):")
    for word, count in repeated_words.items():
        print(f"{word}: {count}")

    print("\nDownloading images...")
    for url in img_scr_list:
        download_image(url)

finally:
    driver.quit()
