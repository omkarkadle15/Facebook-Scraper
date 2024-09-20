import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FacebookGroupScraper:
    def __init__(self, email, password, group_url):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.email = email
        self.password = password
        self.group_url = group_url

    def login(self):
        self.driver.get("https://www.facebook.com")
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_field = self.driver.find_element(By.ID, "pass")
            
            email_field.send_keys(self.email)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='banner']"))
            )
            logging.info("Login successful")

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Login failed: {str(e)}")
            self.driver.quit()
            raise

    def navigate_to_group(self):
        self.driver.get(self.group_url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='main']"))
            )
            logging.info("Successfully navigated to the group")
        except TimeoutException:
            logging.error("Failed to load group page")
            self.driver.quit()
            raise

    def scroll_and_expand(self, max_scrolls=5):
        for _ in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.expand_posts()

    def expand_posts(self):
        try:
            see_more_buttons = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'See more')]")
            for button in see_more_buttons:
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Error expanding posts: {str(e)}")

    def scrape_posts(self, num_posts=10):
        posts = []
        post_elements = self.driver.find_elements(By.XPATH, "//div[@role='article']")

        for index, post in enumerate(post_elements[:num_posts]):
            try:
                logging.info(f"Scraping post {index + 1}/{num_posts}")
                
                # Author
                author_selectors = [
                    ".//h3/span/a", ".//h4/span/a", ".//strong/a",
                    ".//span[contains(@class, 'x3nfvp2')]//a",
                    ".//span[contains(@class, 'x1i10hfl')]//a"
                ]
                author = self.find_element_text(post, author_selectors, "Author")

                # Content
                content_selectors = [
                    ".//div[@data-ad-preview='message']",
                    ".//div[contains(@class, 'xdj266r')]",
                    ".//div[contains(@class, 'x1iorvi4')]",
                    ".//div[contains(@class, 'x1lliihq')]"
                ]
                content = self.find_element_text(post, content_selectors, "Content")

                # Timestamp
                timestamp_selectors = [
                    ".//span[contains(@class, 'x4k7w5x')]",
                    ".//span[contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w')]",
                    ".//a[contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w')]"
                ]
                timestamp = self.find_element_text(post, timestamp_selectors, "Timestamp")

                # Interactions
                interaction_selectors = [
                    ".//span[contains(@class, 'x193iq5w')]",
                    ".//span[contains(@class, 'x1lliihq')]"
                ]
                interactions = []
                for selector in interaction_selectors:
                    interactions = post.find_elements(By.XPATH, selector)
                    if interactions:
                        break

                likes = comments = shares = "N/A"
                if interactions:
                    likes = interactions[0].text if len(interactions) > 0 else "N/A"
                    comments = interactions[1].text if len(interactions) > 1 else "N/A"
                    shares = interactions[2].text if len(interactions) > 2 else "N/A"

                posts.append({
                    "author": author,
                    "content": content,
                    "timestamp": timestamp,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares
                })
                logging.info(f"Successfully scraped post by {author}")

            except Exception as e:
                logging.error(f"Error scraping post {index + 1}: {str(e)}")
                continue

        return posts

    def find_element_text(self, parent, selectors, element_name):
        for selector in selectors:
            try:
                element = parent.find_element(By.XPATH, selector)
                text = element.text.strip()
                if text:
                    logging.info(f"Found {element_name}: {text}")
                    return text
            except NoSuchElementException:
                continue
        logging.warning(f"{element_name} not found")
        return f"Unknown {element_name}"

    def save_page_source(self, filename="facebook_group_page.html"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        logging.info(f"Page source saved to {filename}")

    def run(self):
        try:
            self.login()
            self.navigate_to_group()
            self.scroll_and_expand()
            self.save_page_source()
            posts = self.scrape_posts()
            return posts
        except Exception as e:
            logging.error(f"An error occurred during scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    email = "omkarkadle@gmail.com"
    password = "OmkarKadle@2003"
    group_url = "https://www.facebook.com/groups/2172304909763504"

    scraper = FacebookGroupScraper(email, password, group_url)
    posts = scraper.run()

    print(f"Scraped {len(posts)} posts from the Facebook group.")
    for post in posts:
        print(f"Author: {post['author']}")
        print(f"Content: {post['content'][:100]}...")  # Print first 100 characters
        print(f"Timestamp: {post['timestamp']}")
        print(f"Likes: {post['likes']}, Comments: {post['comments']}, Shares: {post['shares']}")
        print("-" * 50)

if __name__ == "__main__":
    main()