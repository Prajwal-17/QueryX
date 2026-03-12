from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    driver.get("http://localhost:8000")
    
    # Check for console logs
    logs = driver.get_log('browser')
    for log in logs:
        print(f"Browser Log: {log}")
        
    print("Clicking Get Started...")
    start_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "get-started-btn")))
    start_btn.click()
    
    print("Typing message...")
    input_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "user-input")))
    input_field.send_keys("When is ML class?")
    
    print("Adding listener to check DOM for assistant message...")
    driver.execute_script("""
        const oldConsoleError = console.error;
        console.error = function() {
            window.lastConsoleError = arguments;
            oldConsoleError.apply(console, arguments);
        };
    """)
    
    submit_btn = driver.find_element(By.ID, "send-button")
    submit_btn.click()
    
    time.sleep(4)
    
    # Get all assistant messages
    msgs = driver.find_elements(By.CLASS_NAME, "assistant-message")
    for msg in msgs:
        print("Bot Response Found:", msg.text)
        
    err = driver.execute_script("return window.lastConsoleError ? Array.from(window.lastConsoleError).join(' ') : null;")
    if err:
        print("CAUGHT JS ERROR:", err)
        
    # Check for console logs again
    logs = driver.get_log('browser')
    for log in logs:
        print(f"Browser Log: {log}")

except Exception as e:
    print(f"Error during test: {e}")
finally:
    driver.quit()
