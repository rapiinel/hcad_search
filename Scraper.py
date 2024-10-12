import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def similar(search_str, target_str):
    """
    Calculate similarity while being lenient with text and handling FM road numbers properly.
    Returns a score between 0 and 1, where 1 is a perfect match.
    """
    # Convert both strings to lowercase and remove extra whitespace
    search_str = ' '.join(search_str.lower().split())
    target_str = ' '.join(target_str.lower().split())
    
    # Normalize FM road formats first
    def normalize_fm(s):
        # Handle various FM road formats
        s = re.sub(r'\bfm\s*(\d+)\s*rd?\b', r'farm to market \1', s, flags=re.IGNORECASE)
        s = re.sub(r'\bfm\s*(\d+)\b', r'farm to market \1', s, flags=re.IGNORECASE)
        return s
    
    search_str = normalize_fm(search_str)
    target_str = normalize_fm(target_str)
    
    # Extract numbers, but handle special cases
    def extract_numbers(s):
        # Split string into words
        words = s.split()
        numbers = []
        
        # Extract standalone numbers and numbers that are part of FM roads
        for i, word in enumerate(words):
            # Skip numbers that are part of "farm to market X" as they're already normalized
            if i >= 2 and words[i-2:i] == ['farm', 'to', 'market']:
                continue
            
            # Extract other numbers
            if word.isdigit():
                numbers.append(word)
        return numbers
    
    search_numbers = extract_numbers(search_str)
    target_numbers = extract_numbers(target_str)
    
    # If there are numbers in both strings, at least one significant number should match
    if search_numbers and target_numbers:
        if not any(sn == tn for sn, tn in zip(search_numbers, target_numbers)):
            return 0
    
    # Split into words for text comparison
    search_words = set(search_str.split())
    target_words = set(target_str.split())
    
    # Count matching words
    matching_words = search_words.intersection(target_words)
    
    # Calculate score based on how many search words were found
    if not search_words:
        return 0
    
    # Calculate score giving more weight to matches and less penalty for extra words
    score = len(matching_words) / len(search_words)
    
    # Normalize common address terms
    common_replacements = {
        'rd': 'road',
        'st': 'street',
        'ln': 'lane',
        'dr': 'drive',
        'blvd': 'boulevard',
        'hwy': 'highway'
    }
    
    # Apply normalizations and check again if initial score is low
    if score < 0.8:
        normalized_search = search_str
        normalized_target = target_str
        
        for abbr, full in common_replacements.items():
            normalized_search = re.sub(r'\b' + abbr + r'\b', full, normalized_search)
            normalized_target = re.sub(r'\b' + abbr + r'\b', full, normalized_target)
        
        # Recalculate with normalized strings
        norm_search_words = set(normalized_search.split())
        norm_target_words = set(normalized_target.split())
        norm_matching_words = norm_search_words.intersection(norm_target_words)
        
        norm_score = len(norm_matching_words) / len(norm_search_words)
        score = max(score, norm_score)
    
    return score

def find_best_match(search_address, page):
    """Find the best matching address from search results."""
    best_match = None
    best_ratio = 0
    best_index = -1
    
    # Get all search result rows
    rows = page.query_selector_all('.searchtr')
    
    for i, row in enumerate(rows):
        try:
            # Extract address and account number from the row
            address_div = row.query_selector('td div')
            account_div = row.query_selector('td div b')
            
            if not address_div or not account_div:
                continue
            
            # Get the full text and split it to separate name and address
            full_text = address_div.inner_text()
            text_parts = full_text.split('\n')
            
            if len(text_parts) < 2:
                continue
            
            address_text = text_parts[1].strip()
            account_number = account_div.inner_text().strip()
            
            # Check if account number is 13 digits
            if not account_number.isdigit() or len(account_number) != 13:
                continue
            
            # Calculate similarity
            similarity = similar(search_address, address_text)
            
            # Update best match if this is better
            if similarity > best_ratio:
                best_ratio = similarity
                best_index = i
                
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue
    
    # Return the best match if it's above a threshold
    if best_ratio > 0.6 and best_index >= 0:  # Adjusted threshold to be more lenient
        return best_index
    return None

def extract_info(html):
    # [Previous extract_info function remains the same]
    soup = BeautifulSoup(html, 'html.parser')
    info = {}
    
    try:
        # Extract account, name, and mailing address
        info['Account'] = soup.select_one('.whitebox-medium-font:-soup-contains("Account:") + div')
        info['Account'] = info['Account'].text.strip() if info['Account'] else "N/A"
        
        info['Name'] = soup.select_one('.whitebox-medium-font:-soup-contains("Name:") + div')
        info['Name'] = info['Name'].text.strip() if info['Name'] else "N/A"
        
        info['Mailing Address'] = soup.select_one('.whitebox-medium-font:-soup-contains("Mailing Address:") + span')
        info['Mailing Address'] = info['Mailing Address'].text.strip() if info['Mailing Address'] else "N/A"
        
        # Extract valuations
        info['Land Valuation'] = soup.select_one('#ValuationComponent > div:nth-child(1) > div.shadow-sm.p-3.mb-0.bg-white.rounded > div:nth-child(2) > div:nth-child(1) > table > tr:nth-child(1) > td:nth-child(2) > div')
        info['Land Valuation'] = info['Land Valuation'].text.strip() if info['Land Valuation'] else "N/A"
        
        info['Improvement Valuation'] = soup.select_one('#ValuationComponent > div:nth-child(1) > div.shadow-sm.p-3.mb-0.bg-white.rounded > div:nth-child(2) > div:nth-child(1) > table > tr:nth-child(2) > td:nth-child(2) > div')
        info['Improvement Valuation'] = info['Improvement Valuation'].text.strip() if info['Improvement Valuation'] else "N/A"
        
        info['Market Valuation'] = soup.select_one('#ValuationComponent > div:nth-child(1) > div.shadow-sm.p-3.mb-0.bg-white.rounded > div:nth-child(2) > div:nth-child(1) > table > tr:nth-child(3) > td:nth-child(2) > div')
        info['Market Valuation'] = info['Market Valuation'].text.strip() if info['Market Valuation'] else "N/A"
        
        info['Appraised Valuation'] = soup.select_one('#ValuationComponent > div:nth-child(1) > div.shadow-sm.p-3.mb-0.bg-white.rounded > div:nth-child(2) > div:nth-child(1) > table > tr:nth-child(4) > td:nth-child(2) > div')
        info['Appraised Valuation'] = info['Appraised Valuation'].text.strip() if info['Appraised Valuation'] else "N/A"
        
        # Extract other details
        info['Legal Description'] = soup.select_one('.row.whitebox-medium-font.p-1:-soup-contains("Legal Description") .col')
        info['Legal Description'] = info['Legal Description'].text.strip() if info['Legal Description'] else "N/A"
        
        info['Land'] = soup.select_one('.row.whitebox-medium-font.p-1:-soup-contains("Land") .col')
        info['Land'] = info['Land'].text.strip() if info['Land'] else "N/A"
        
        info['Building Area'] = soup.select_one('.row.whitebox-medium-font.p-1:-soup-contains("Building Area") .col')
        info['Building Area'] = info['Building Area'].text.strip() if info['Building Area'] else "N/A"
        
        info['State Class Code'] = soup.select_one('table:-soup-contains("State Class Code") td')
        info['State Class Code'] = info['State Class Code'].text.strip() if info['State Class Code'] else "N/A"
        
        # Extract building details if available
        building_summary = soup.select_one('#BuildingSummaryComponent')
        if building_summary:
            info['Year Built'] = soup.select_one('#BuildingView > div > table > tbody > tr:nth-child(1) > td:nth-child(3)')
            info['Year Built'] = info['Year Built'].text.strip() if info['Year Built'] else "N/A"
            
            info['Type'] = soup.select_one('#BuildingView > div > table > tbody > tr:nth-child(1) > td:nth-child(4)')
            info['Type'] = info['Type'].text.strip() if info['Type'] else "N/A"
            
            info['Impr Sq Ft'] = soup.select_one('#BuildingView > div > table > tbody > tr:nth-child(1) > td:nth-child(7)')
            info['Impr Sq Ft'] = info['Impr Sq Ft'].text.strip() if info['Impr Sq Ft'] else "N/A"
        else:
            info['Year Built'] = info['Type'] = info['Impr Sq Ft'] = "N/A"
    
    except Exception as e:
        print(f"Error extracting information: {str(e)}")
        with open("debug_output.html", "w", encoding="utf-8") as f:
            f.write(html)
    
    return info

def run(playwright, addresses_df):
    start_url = "https://search.hcad.org"
    chrome = playwright.chromium
    browser = chrome.launch()
    page = browser.new_page()
    
    results = []

    try:
        for _, row in addresses_df.iterrows():
            address = row['Search Address']
            try:
                print(f"\nProcessing address: {address}")
                
                # Navigate to start page for each search
                page.goto(start_url)

                # Fill in the search input
                page.fill('input.searchTerm', address)
                
                # Wait for search results
                page.wait_for_selector('.searchtr', timeout=50000)
                
                # Find the best matching result
                best_match_index = find_best_match(address, page)
                
                if best_match_index is not None:
                    # Get all rows again and click the best match
                    rows = page.query_selector_all('.searchtr')
                    best_row = rows[best_match_index]
                    
                    # Get the account number before clicking
                    account_div = best_row.query_selector('td div b')
                    account_number = account_div.inner_text() if account_div else "N/A"
                    print(f"Found best matching account number: {account_number}")
                    
                    # Click the best matching result
                    best_row.click()
                    
                    # Wait for navigation and content load
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(15000)

                    # Get HTML content and extract information
                    html = page.content()
                    info = extract_info(html)
                    info['Account Number'] = str(account_number)
                    info['Search Keyword'] = address
                    info['Realnex Key'] = row['Key']
                    pd.DataFrame([info]).to_csv(f'temp/{row['Key']}.csv', index=False)
                    results.append(info)
                else:
                    print(f"No suitable match found for address: {address}")
                    continue

            except Exception as e:
                print(f"An error occurred while processing address {address}: {str(e)}")
                continue
        
        # Create DataFrame and save results
        if results:
            df = pd.DataFrame(results)
            
            # Remove 'Mailing Address' column and swap 'Name' and 'Mailing Address'
            df.rename(columns={'Account': 'Name', 'Name': 'Mailing Address'}, inplace=True)
            del df['Mailing Address']
            df = df[['Search Keyword', 'Account Number'] + [x for x in df if x not in ['Search Keyword', 'Account Number']]]

            # Save to CSV
            csv_filename = 'Property_info_results.csv'
            df.to_csv(csv_filename, index=False)
            print(f"Information saved to {csv_filename}")
        else:
            print("No results were collected.")

    finally:
        browser.close()

# Load addresses and run the script
file_path = 'Property_address.csv'
address_df = pd.read_csv(file_path)

with sync_playwright() as playwright:
    run(playwright, address_df)