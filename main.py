from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(executable_path="C:\\Users\\tpsuc\\Downloads\\Duplicate Content Checker\\chromedriver.exe", options=options)

driver.get("https://example.com")
driver.save_screenshot('C:\\Users\\tpsuc\\Downloads\\Duplicate Content Checker\\screenshots\\screenshot.png')
driver.quit()
