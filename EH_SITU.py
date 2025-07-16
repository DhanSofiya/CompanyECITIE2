from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# === Setup Firefox ===
options = Options()
driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 15)

driver.get("https://ecitie2.unikl.edu.my/index.php")
input("✅ Please log in and stay on the company list page. Press ENTER to start...")

filtered_companies = []

valid_nobs = {
    "SOFTWARE ENGINEERING",
    "INFORMATION TECHNOLOGY",
    "INFORMATION TECHNOLOGY (IT)"
}
valid_states = {
    "WILAYAH PERSEKUTUAN KUALA LUMPUR",
    "NEGERI SEMBILAN"
}

def exit_program():
    if filtered_companies:
        df = pd.DataFrame(filtered_companies)
        df.to_excel("filtered_companies.xlsx", index=False)
        print(f"\n📁 Saved {len(filtered_companies)} matching companies to filtered_companies.xlsx")
    else:
        print("\n📭 No matching companies found.")
    print("👋 Exiting program and closing browser...")
    driver.quit()
    exit()

def get_active_page_number():
    try:
        text = driver.find_element(By.XPATH, "//li[contains(@class, 'active')]/a").text.strip()
        return int(text)
    except:
        return None

def go_to_previous_page():
    try:
        current_page = get_active_page_number()
        prev_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@id='dynamicFormTable_263_previous']/a[@class='page-link']")
        ))
        driver.execute_script("arguments[0].click();", prev_btn)
        time.sleep(2)
        new_page = get_active_page_number()
        if new_page and new_page != current_page:
            print(f"⬅️ Moved from page {current_page} to {new_page}")
            return True
        else:
            print(f"⚠️ Still on page {current_page} — reached beginning or stuck.")
            return False
    except:
        print("❌ Could not go to previous page.")
        return False

def go_to_page_228():
    while True:
        current_page = get_active_page_number()
        if current_page is None:
            print("❌ Could not detect active page.")
            exit_program()
        if current_page == 228:
            print("🎯 Reached page 228. Starting scrape...")
            break
        elif current_page < 228:
            print(f"⚠️ Current page {current_page} is before page 228. Manual correction needed.")
            exit_program()
        else:
            print(f"↩️ Navigating to page 228 from page {current_page}...")
            if not go_to_previous_page():
                print("❌ Cannot go further back.")
                exit_program()

def scrape_companies_on_page():
    current_page = get_active_page_number()
    print(f"\n📄 Scraping page {current_page}...")

    try:
        links = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'POPUP_PAGE')]")
        print(f"🔍 Found {len(links)} company links.")

        for i in range(len(links)):
            links = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'POPUP_PAGE')]")
            driver.execute_script("arguments[0].click();", links[i])
            wait.until(EC.presence_of_element_located((By.ID, "modalPage")))
            time.sleep(1)

            modal = driver.find_element(By.ID, "modalPage")
            style = modal.get_attribute("style") or ""
            class_list = modal.get_attribute("class") or ""

            if "display: block" in style and "show" in class_list.split():
                print("✅ Modal is visible.")
                try:
                    iframe = modal.find_element(By.TAG_NAME, "iframe")
                    driver.switch_to.frame(iframe)
                    time.sleep(1)

                    try:
                        nob = driver.find_element(By.ID, "dform_258_item_1").text.strip()
                    except:
                        nob = "N/A"

                    try:
                        state = driver.find_element(By.ID, "dform_258_item_9").text.strip()
                    except:
                        state = "N/A"

                    try:
                        name = driver.find_element(By.ID, "dform_258_item_3").text.strip()
                    except:
                        name = "N/A"

                    print(f"🏢 Name             : {name}")
                    print(f"🧾 Nature of Biz    : {nob}")
                    print(f"🌍 State            : {state}")

                    if nob.upper() in valid_nobs and state.upper() in valid_states:
                        filtered_companies.append({
                            "Name": name,
                            "Nature of Business": nob,
                            "State": state
                        })
                        print("✅ Accepted and saved.")
                    else:
                        print("❌ Not matching filter. Skipped.")

                    driver.switch_to.default_content()

                except Exception as e:
                    print(f"❌ Error in iframe: {type(e).__name__}")
                    driver.switch_to.default_content()
            else:
                print("❌ Modal not detected.")

            # Close modal
            try:
                modal = driver.find_element(By.ID, "modalPage")
                close = modal.find_element(By.CSS_SELECTOR, "a[data-dismiss='modal']")
                driver.execute_script("arguments[0].click();", close)
                time.sleep(1)
            except:
                print("⚠️ Could not close modal.")

    except Exception as e:
        print(f"\n❌ Scraping error: {type(e).__name__}: {e}")

# === Scrape 100 Pages Only ===
def run_limited_pages(limit=100):
    count = 0
    while count < limit:
        scrape_companies_on_page()
        count += 1
        if not go_to_previous_page():
            break
    print(f"\n⏸ Reached {count} pages.")
    choice = input("🔁 Continue scraping more (C) or Quit (Q)? ").strip().lower()
    if choice == 'q':
        exit_program()
    else:
        run_limited_pages(limit)

# === Start from Page 228 ===
go_to_page_228()
run_limited_pages(100)
