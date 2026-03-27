from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import time

def ddg_click_third_result(query: str):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    # Result item + title selectors (primary + fallback)
    RESULT_ITEM = "article[data-testid='result'], article.result"
    RESULT_TITLE = "a[data-testid='result-title-a'], h2 a[href]"

    try:
        print("[1] Opening DuckDuckGo…")
        driver.get("https://duckduckgo.com/")

        # Search box can be 'searchbox_input' or fallback 'search_form_input'
        print("[2] Waiting for search box…")
        try:
            q = wait.until(EC.visibility_of_element_located((By.ID, "searchbox_input")))
        except TimeoutException:
            q = wait.until(EC.visibility_of_element_located((By.ID, "search_form_input")))

        q.clear()
        q.send_keys(query)
        q.send_keys(Keys.RETURN)

        print("[3] Waiting for results container…")
        # On most layouts, results are within #links; fallback to presence of result articles
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#links")))
        except TimeoutException:
            # Fallback: wait for at least one result item
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RESULT_ITEM)))

        # Helper: get current results
        def get_results():
            return driver.find_elements(By.CSS_SELECTOR, RESULT_ITEM)

        # [4] Scroll until we have at least 3 results or we can’t scroll further
        print("[4] Scrolling until at least 3 results appear…")
        last_height = driver.execute_script("return document.body.scrollHeight")
        start = time.time()

        while True:
            results = get_results()
            print(f"    -> Currently found {len(results)} result(s)")
            if len(results) >= 3:
                break

            # Scroll down a bit to trigger more results
            driver.execute_script("window.scrollBy(0, 1200);")
            time.sleep(0.8)

            # Check if page height increased (i.e., more content loaded)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # No more content; stop trying
                print("    -> No further content to load.")
                break
            last_height = new_height

            # Safety timeout (avoid infinite loop)
            if time.time() - start > 20:
                print("    -> Timeout while waiting for enough results.")
                break

        # Refresh results after scrolling
        results = get_results()
        if len(results) < 3:
            raise RuntimeError(f"Only found {len(results)} result(s); cannot click the 3rd.")

        # [5] Work with the 3rd result (0-based index)
        third = results[2]

        # Scroll the 3rd result into center view (more reliable than pixel scroll)
        print("[5] Scrolling the 3rd result into view…")
        driver.execute_script("arguments[0].scrollIntoView({behavior:'instant', block:'center'});", third)
        time.sleep(0.4)

        # [6] Find its title link inside this result and click
        print("[6] Locating title link inside the 3rd result…")
        link = WebDriverWait(third, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, RESULT_TITLE))
        )

        try:
            print("[7] Clicking the 3rd result (normal click)…")
            link.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            # Fallback to JS click if something overlays or steals focus
            print("[7-Fallback] Normal click failed; attempting JS click…")
            driver.execute_script("arguments[0].click();", link)

        # Optional: wait for navigation (URL change)
        WebDriverWait(driver, 15).until(lambda d: d.current_url and "duckduckgo.com" not in d.current_url)
        print("[8] Navigation succeeded. Current URL:", driver.current_url)

        # Keep the tab visible for a moment (demo)
        time.sleep(2)

    finally:
        driver.quit()

if __name__ == "__main__":
    ddg_click_third_result("selenium webdriver explicit waits")
    time.sleep(2)