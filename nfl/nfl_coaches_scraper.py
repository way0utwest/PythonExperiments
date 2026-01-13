from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    # Comment out headless to see what's happening
    # options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

def get_coaches_list(driver, url):
    """Get list of all coaches from the main page"""
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    
    coaches = []
    
    try:
        # Find the coaches table
        table = driver.find_element(By.ID, 'coaches')
        tbody = table.find_element(By.TAG_NAME, 'tbody')
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        
        print(f"Found {len(rows)} rows in table")
        
        for row in rows:
            try:
                # Skip header rows
                if 'thead' in row.get_attribute('class') or '':
                    continue
                
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) < 7:
                    continue
                
                # Get coach name and URL from first cell
                name_cell = row.find_element(By.CSS_SELECTOR, 'th[data-stat="coach"]')
                link = name_cell.find_element(By.TAG_NAME, 'a')
                coach_name = link.text.strip()
                coach_url = link.get_attribute('href')
                
                # Get stats from cells
                yrs = cells[0].text.strip()  # data-stat="yrs"
                from_year = cells[1].text.strip()  # data-stat="year_min"
                to_year = cells[2].text.strip()  # data-stat="year_max"
                games = cells[3].text.strip()  # data-stat="g"
                wins = cells[4].text.strip()  # data-stat="w"
                losses = cells[5].text.strip()  # data-stat="l"
                ties = cells[6].text.strip()  # data-stat="t"
                
                if coach_name and coach_url:
                    coaches.append({
                        'name': coach_name,
                        'url': coach_url,
                        'yrs': yrs,
                        'from': from_year,
                        'to': to_year,
                        'g': games,
                        'w': wins,
                        'l': losses,
                        't': ties
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error getting coaches list: {e}")
        import traceback
        traceback.print_exc()
    
    return coaches

def get_coach_career(driver, coach_url):
    """Get coaching career details for a specific coach"""
    driver.get(coach_url)
    time.sleep(3)  # Wait for page to load
    
    career_data = []
    try:
        # Pro-Football-Reference often puts tables in HTML comments
        # We need to use JavaScript to extract them
        driver.execute_script("""
            var comments = document.evaluate('//comment()', document, null, XPathResult.ANY_TYPE, null);
            var comment = comments.iterateNext();
            while (comment) {
                if (comment.nodeValue.indexOf('id="coaching_record"') !== -1) {
                    var div = document.createElement('div');
                    div.innerHTML = comment.nodeValue;
                    comment.parentNode.replaceChild(div, comment);
                    break;
                }
                comment = comments.iterateNext();
            }
        """)
        
        time.sleep(1)
        
        # Now try to find the table
        table = driver.find_element(By.ID, 'coaching_record')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        
        for row in rows:
            try:
                # Get all cells (th and td)
                year_cell = row.find_element(By.CSS_SELECTOR, '[data-stat="year"]')
                team_cell = row.find_element(By.CSS_SELECTOR, '[data-stat="team"]')
                
                year = year_cell.text.strip()
                
                # Get the team abbreviation from the link if it exists
                try:
                    team_link = team_cell.find_element(By.TAG_NAME, 'a')
                    team_url = team_link.get_attribute('href')
                    # Extract team code from URL like /teams/chi/2024.htm
                    if '/teams/' in team_url:
                        team_code = team_url.split('/teams/')[1].split('/')[0].upper()
                    else:
                        team_code = team_link.text.strip()
                except:
                    team_code = team_cell.text.strip()
                
                # Skip empty or summary rows
                if year and team_code and year.isdigit():
                    career_data.append((team_code, year))
            except:
                continue
                
    except Exception as e:
        print(f"Error getting career data: {e}")
        import traceback
        traceback.print_exc()
    
    return career_data

def main():
    base_url = 'https://www.pro-football-reference.com/coaches/'
    
    print("Setting up browser...")
    driver = setup_driver()
    
    try:
        print("Fetching coaches list...")
        coaches = get_coaches_list(driver, base_url)
        print(f"Found {len(coaches)} coaches")
        
        if len(coaches) == 0:
            print("No coaches found. The page structure may have changed.")
            return
        
        # Save coaches list to CSV
        coaches_list_file = 'nfl_coaches_list.csv'
        with open(coaches_list_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'URL', 'Yrs', 'From', 'To', 'G', 'W', 'L', 'T'])
            
            for coach in coaches:
                writer.writerow([
                    coach['name'],
                    coach['url'],
                    coach['yrs'],
                    coach['from'],
                    coach['to'],
                    coach['g'],
                    coach['w'],
                    coach['l'],
                    coach['t']
                ])
        
        print(f"Coaches list saved to {coaches_list_file}")
        
        # Prepare CSV output for career history
        output_file = 'nfl_coaches_history.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Team', 'Year', 'Coach Name'])
            
            # Loop through each coach
            for i, coach in enumerate(coaches, 1):
                coach_name = coach['name']
                coach_url = coach['url']
                
                print(f"Processing {i}/{len(coaches)}: {coach_name}")
                
                try:
                    career = get_coach_career(driver, coach_url)
                    for team, year in career:
                        writer.writerow([team, year, coach_name])
                    
                    # Be polite - add delay between requests
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"Error processing {coach_name}: {e}")
                    continue
        
        print(f"\nDone! Career history saved to {output_file}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
