from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time

def scrape_coaching_stats(url):
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        driver.get(url)
        
        # Wait for the table to load
        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.ID, "coach")))
        
        # Give it a moment to fully render
        time.sleep(2)
        
        # Find all rows in the tbody
        rows = table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        
        # Prepare data list
        coaching_data = []
        
        # Extract data from each row
        for row in rows:
            # Skip rows that are headers or empty
            if 'thead' in row.get_attribute('class') or not row.text.strip():
                continue
            
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 5:
                continue
            
            # Extract year
            year_cell = row.find_element(By.TAG_NAME, "th")
            year = year_cell.text.strip()
            
            # Extract other data
            team = cells[1].text.strip()
            wins = cells[3].text.strip()
            losses = cells[4].text.strip()
            ties = cells[5].text.strip() if len(cells) > 5 else "0"
            
            # Get coach name from page title or header
            if not coaching_data:  # First row, get the coach name
                page_title = driver.title
                coach_name = page_title.split(' Stats')[0].strip()
            
            coaching_data.append({
                'name': coach_name,
                'year': year,
                'team': team,
                'wins': wins,
                'losses': losses,
                'ties': ties
            })
        
        # Write to CSV
        output_file = 'coaching_stats.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'year', 'team', 'wins', 'losses', 'ties']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(coaching_data)
        
        print(f"Successfully scraped {len(coaching_data)} records")
        print(f"Data saved to {output_file}")
        
        # Print first few rows as preview
        print("\nPreview:")
        for i, row in enumerate(coaching_data[:5]):
            print(row)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.pro-football-reference.com/coaches/HalaGe0.htm"
    scrape_coaching_stats(url)