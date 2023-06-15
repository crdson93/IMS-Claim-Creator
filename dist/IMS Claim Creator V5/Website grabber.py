from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Setup Chrome options
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")

# Setup the driver
webdriver_service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# Get the current page source
source = driver.page_source

# Print the page source
print(source)

# If you just want the visible text, not the HTML source, use
print(driver.find_element(By.TAG_NAME, 'body').text)

print("Got here")

# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222