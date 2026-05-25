# Copyright 2026 by Christian Brossette
__author__ = "Christian Brossette"
__copyright__ = "Copyright 2026"
__credits__ = ["Christian Brossette"]
__license__ = "GPL"
__version__ = "0.6"
__maintainer__ = "Christian Brossette"
__email__ = "info@gibtesheuteschnitzel.de"
__status__ = ""

import re
import time
import requests
import os
import json
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schnitzel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def is_today(day):
    """
    Check if the given day object represents today's date.
    
    Args:
        day (dict): Day object from API response
        
    Returns:
        bool: True if the day is today, False otherwise
    """
    try:
        # Parse the input date string
        input_date = datetime.strptime(day.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ')
        input_date = input_date.replace(tzinfo=timezone.utc)  # Ensure UTC timezone

        # Get today's date in UTC
        today = datetime.now(timezone.utc).date()

        # Compare only the date parts
        is_today_result = input_date.date() == today
        logger.debug(f"Checking date: {input_date.date()} vs today: {today} -> {is_today_result}")
        return is_today_result
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing date from day object: {e}")
        return False


def find_schnitzel_items(day):
    """
    Search for schnitzel items in a day's menu.
    
    Args:
        day (dict): Day object containing counters/menu items        
    Returns:
        list: List of menu items containing schnitzel
    """
    keywords = [r"schnitzel"]
    schnitzel_items = []
    
    for item in day.get('counters', []):
        item_text = json.dumps(item, ensure_ascii=False)
        for keyword in keywords:
            if re.search(keyword, item_text, re.IGNORECASE):
                schnitzel_items.append(item)
                logger.debug(f"Found schnitzel item with keyword '{keyword}': {item}")
                break  # Don't add the same item multiple times
    
    logger.info(f"Found {len(schnitzel_items)} schnitzel items")
    return schnitzel_items


def get_schnitzel(api_url, api_key, max_retries=3):
    """
    Fetch menu data from API and check for schnitzel availability today.
    
    Args:
        api_url (str): API endpoint URL
        api_key (str): API authentication key
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        tuple: (answer, data, isToday) where answer is 'ja'/'nein', data is API response, isToday is boolean
    """
    headers = {'Authorization': f'Bearer {api_key}'}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching data from API (attempt {attempt + 1}/{max_retries})")
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raises exception for HTTP errors
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}")

            data = response.json()  # Parse JSON response
            logger.info("Successfully fetched API data")

            # Iterate over the menu days
            for day in data.get('days', []):
                is_today_result = is_today(day)
                if is_today_result:
                    # Only use basic schnitzel matching (extended=False)
                    schnitzel = find_schnitzel_items(day)
                    answer = 'ja' if schnitzel else 'nein'
                    logger.info(f"Today's schnitzel status: {answer}")
                    return (answer, data, True)
                else:
                    logger.debug("Found non-past day but it's not today")
                    break  # Found future day, stop looking


            # No today's menu found
            logger.warning("No menu found for today")
            return ('nein', data, False)
            
        except requests.RequestException as e:
            logger.error(f"API request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error("All retry attempts failed")
                raise
            # Exponential backoff
            sleep_time = 2 ** attempt
            logger.info(f"Waiting {sleep_time} seconds before retry...")
            time.sleep(sleep_time)


def update_stats_file(answer, data, isToday):
    """
    Update the statistics file with today's schnitzel status.
    
    Args:
        answer (str): 'ja' or 'nein'
        data (dict): API response data
        isToday (bool): Whether the check is for today
    """
    if not isToday:
        logger.info("Not updating stats - not checking for today")
        return
        
    stats_file = 'stats.txt'
    today_date = time.strftime("%x")
    logger.info(f"Updating stats for date: {today_date} with answer: {answer}")
    
    try:
        # Read existing file
        try:
            with open(stats_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.info("Stats file not found, creating new one")
            lines = []

        # Check if today already has an entry
        entry_updated = False
        if lines:
            last_line = lines[-1].strip()
            if last_line.startswith(today_date):
                # Today already has an entry
                current_answer = last_line.split('_')[-1]
                if current_answer != answer and answer != 'nein':
                    # Update existing entry if new answer is not 'nein'
                    lines[-1] = f"{today_date}_{answer}\n"
                    entry_updated = True
                    logger.info(f"Updated existing entry from {current_answer} to {answer}")
                else:
                    logger.info("Entry for today already exists and doesn't need updating")
            else:
                # Add new entry for today
                lines.append(f"{today_date}_{answer}\n")
                entry_updated = True
                logger.info("Added new entry for today")
        else:
            # First entry ever
            lines.append(f"{today_date}_{answer}\n")
            entry_updated = True
            logger.info("Created first stats entry")

        # Write back to file
        if entry_updated:
            with open(stats_file, 'w') as f:
                f.writelines(lines)
            logger.info("Stats file updated successfully")
            
        # Archive menu
        write_menue_to_archive(data)
                
    except Exception as e:
        logger.error(f"Error updating stats file: {e}")


def write_menue_to_archive(data):
    """
    Archive the menu data to a dated directory structure.
    Each run gets a new number per day.
    """
    try:
        current_date = datetime.now()
        year = current_date.strftime("%Y")
        month = current_date.strftime("%m")
        day = current_date.strftime("%d")

        directory_path = os.path.join(os.getcwd(), f"menue_archive/{year}/{month}/{day}")
        os.makedirs(directory_path, exist_ok=True)

        # Determine next run number for today
        existing = [fname for fname in os.listdir(directory_path) if fname.startswith(f"mensaar_menue_{year}_{month}_{day}_")]
        run_number = len(existing) + 1
        file_name = f"mensaar_menue_{year}_{month}_{day}_{run_number:02d}.json"
        file_path = os.path.join(directory_path, file_name)

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        logger.info(f"Menu archived to: {file_path}")

    except Exception as e:
        logger.error(f"Error archiving menu: {e}")


def calculate_p_schnitzel():
    """
    Calculate schnitzel probability based on historical data.
    Returns current day's status, not the last entry from stats.
    
    Returns:
        tuple: (statistics_string, today_answer)
    """
    try:
        ja_count = 0
        total_count = 0
        first_line = None
        today_date = time.strftime("%x")
        today_answer = "nein"  # Default to "nein" if nothing found for today
        
        with open('webpage/stats.txt', 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                if first_line is None:
                    first_line = line
                
                try:
                    date_part = line.split('_')[0]
                    answer = line.split('_')[-1]
                    
                    # Check if this line is for today
                    if date_part == today_date:
                        today_answer = answer
                        logger.debug(f"Found today's entry: {answer}")
                    
                    # Count for statistics
                    if answer == 'ja':
                        ja_count += 1
                    total_count += 1
                    
                except IndexError:
                    logger.warning(f"Malformed line {line_num} in stats file: {line}")
                    continue

        if total_count == 0:
            logger.warning("No valid entries in stats file")
            return ("Keine Daten verfügbar", "nein")

        # Calculate percentage
        p_schnitzel = 100.0 * (float(ja_count) / float(total_count))
        
        # Format first date
        if first_line:
            wrong_date = first_line.split('_')[0].split('/')
            normal_date = '.'.join([wrong_date[1], wrong_date[0], wrong_date[2]])
        else:
            normal_date = "unbekannt"
            
        stats_string = f"{p_schnitzel:3.2f}% Schnitzel seit dem {normal_date}"
        logger.info(f"Calculated statistics: {stats_string}, Today's status: {today_answer}")
        
        return (stats_string, today_answer)
        
    except FileNotFoundError:
        logger.error("Stats file not found")
        return ("Keine Statistiken verfügbar", "nein")
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return ("Fehler beim Berechnen der Statistiken", "nein")


def write_schnitzel_page(answer, stats):
    """
    Generate the HTML webpage with schnitzel status.
    
    Args:
        answer (str): Current schnitzel status ('ja'/'nein')
        stats (str): Statistics string
    """
    try:
        # Ensure webpage directory exists
        os.makedirs('webpage', exist_ok=True)
        
        with open('webpage/index.html', 'w') as f:
            page_begin = """<!DOCTYPE html>

                <html>

                <head>
                    <meta charset="UTF-8" />
                    <title>Gibt es heute Schnitzel an der Universität des Saarlandes?</title>
                    <link rel="icon" href="icon.svg" type="image/svg+xml">
                    <meta name="description" content="Ja/Nein" />

                    <style>
                        h1 {
                            font-size: 7em;
                            font-family: Helvetica;
                            text-align: center;
                            padding-top: 3cm;
                            top: 40px;
                        }

                        h2 {
                            font-size: 1em;
                            font-family: Helvetica;
                            text-align: center;
                        }

                        h3 {
                            font-size: .7em;
                            font-family: Helvetica;
                            padding-top: 3cm;
                            text-align: center;
                            top: 40px;
                        }
                    </style>
                </head>

            <body>
            """

            main_content = f"<h1>{answer}</h1>"
            statistic = f"<h2>{stats}</h2>"
            link = '<h2><a href="https://mensaar.de/#/menu/sb">Mensaar Speiseplan</a></h2>'
            fancy_plots = '<h2><a href="evaluation.html">Auswertung (Neu!)</a></h2>'

            page_end = """
                <footer>
                    <h3>
                        <a href='datenschutz.html'>Datenschutzerklaerung</a> |
                        <a href='changelog.html'>Changelog</a> |
                        <a href='https://github.com/ChristianBrossette/gibtesheuteschnitzel'>GitHub</a>
                    </h3>
                </footer>
            </body>
            </html>"""

            f.write(page_begin)
            f.write(main_content)
            f.write(statistic)
            f.write(link)
            f.write(fancy_plots)
            f.write(page_end)
            
        logger.info("Webpage generated successfully")
        
    except Exception as e:
        logger.error(f"Error writing webpage: {e}")


def load_config(file_path):
    """
    Load configuration from JSON file.
    
    Args:
        file_path (str): Path to configuration file
        
    Returns:
        dict: Configuration data
    """
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        logger.info(f"Configuration loaded from {file_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        raise


def main():
    """Main execution function with error handling."""
    try:
        logger.info("Starting schnitzel check application")
        
        config = load_config('config.json')
        api_url_baseData = config['api_url_baseData']
        api_url_menu = config['api_url_menu']
        api_key = config['api_key']
        
        answer, data, isToday = get_schnitzel(api_url_menu, api_key)
        
        update_stats_file(answer, data, isToday)
        
        stats, final_answer = calculate_p_schnitzel()
        
        write_schnitzel_page(final_answer, stats)
        
        logger.info(f"Application completed successfully. Schnitzel today: {final_answer}")
        
    except Exception as e:
        logger.error(f"Application failed with error: {e}")
        # Try to write error page
        try:
            write_schnitzel_page("Fehler", "Daten konnten nicht geladen werden")
            logger.info("Error page generated")
        except Exception as page_error:
            logger.error(f"Could not generate error page: {page_error}")
        raise

if __name__ == '__main__':
    main()
