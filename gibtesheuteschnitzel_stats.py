# Copyright 2025 by Christian Brossette
__author__ = "Christian Brossette"
__copyright__ = "Copyright 2025"
__credits__ = ["Christian Brossette"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Christian Brossette"
__email__ = "info@gibtesheuteschnitzel.de"
__status__ = ""

import re
import time
import requests
import os
import json
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from collections import defaultdict


def is_today(day):
    # Parse the input date string
    input_date = datetime.strptime(day.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ')
    input_date = input_date.replace(tzinfo=timezone.utc)  # Ensure UTC timezone

    # Get today's date in UTC
    today = datetime.now(timezone.utc).date()

    # Compare only the date parts
    return input_date.date() == today


def get_schnitzel(api_url, api_key):
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")

    data = response.json()  # Parse JSON response

    # iterate over the menu days
    for day in data.get('days', []):
        if not day.get('isPast'):
            schnitzel = [
                item for item in day.get('counters', []) if re.search(r"Schnitzel", json.dumps(item), re.IGNORECASE)
                ]
            isToday = is_today(day)
            break
        else:
            continue

    answer = 'nein'
    if schnitzel and isToday:
        answer = 'ja'

    return (answer, data, isToday)


def update_stats_file(answer, data, isToday):
    f = open('stats.txt', 'r+')
    # get the last entry of the stat file
    last_line = None
    for line in f:
        last_line = line

    today_date = time.strftime("%x")

    if isToday:
        if today_date == last_line.split('_')[0]:
            if last_line.split('_')[-1].strip() != answer and answer != 'nein':
                f_ = open('stats.txt', 'r')
                lines_ = f_.readlines()
                lines_ = lines_[:-1]
                f_.close()
                f_ = open('stats.txt', 'w')
                for l_ in lines_:
                    f_.write(l_)
                f_.write(str(today_date + '_' + answer + '\n'))
                f_.close()
                write_menue_to_archive(data)
        else:
            f.write(str(today_date + '_' + answer + '\n'))
            write_menue_to_archive(data)
        f.close()


def write_menue_to_archive(data):
    current_date = datetime.now()
    year = current_date.strftime("%Y")
    month = current_date.strftime("%m")
    day = current_date.strftime("%d")

    directory_path = os.path.join(os.getcwd(), f"menue_archive/{year}/{month}/{day}")
    os.makedirs(directory_path, exist_ok=True)

    file_name = f"mensaar_menue_{year}_{month}_{day}.json"
    file_path = os.path.join(directory_path, file_name)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def calculate_p_schnitzel():
    ja = 0
    total = 0
    with open('stats.txt', 'r') as f:
        for line in f:
            if total == 0:
                # get the first entry of the stat file
                first_line = line
            if line.split('_')[-1].strip() == 'ja':
                ja += 1
                total += 1
            else:
                total += 1
            last_line = line

    p_schnitzel = 100.0 * (float(ja) / float(total))
    wrong_date = first_line.split('_')[0].split('/')
    normal_date = '.'.join([wrong_date[1], wrong_date[0], wrong_date[2]])
    answer = last_line.split('_')[-1].replace('\r', '').replace('\n', '')
    return 	(str('%3.2f' % (p_schnitzel)) + '% Schnitzel seit dem ' + str(normal_date), answer)


def makeFancyPlots():
    # Specify file path
    file_path = 'stats.txt'

    # Initialize data storage
    current_year_data = defaultdict(lambda: {'ja': 0, 'nein': 0})
    previous_years_data = defaultdict(lambda: {'ja': 0, 'nein': 0})

    # Read the file line by line
    with open(file_path, 'r') as file:
        for line in file:
            # Split each line based on the separator
            parts = line.strip().split('_')
            
            # Extract date and value from the parts
            date_str, value = parts[0], parts[1]
            
            # Convert date string to datetime object
            date = datetime.strptime(date_str, "%m/%d/%y")
            month_year = date.strftime('%Y-%m')

            # Update data based on current or previous years
            if date.year == datetime.now().year:
                current_year_data[month_year][value] += 1
            else:
                previous_years_data[month_year][value] += 1

    # Convert data to a format suitable for plotting
    current_year_labels, current_year_values = zip(*current_year_data.items())
    previous_years_labels, previous_years_values = zip(*previous_years_data.items())

    # Increase figure size and set dpi for better resolution
    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)  # Adjust figsize and dpi as needed

    # Plot for the current year and save to disk with increased resolution
    ax.bar(current_year_labels, [v['ja'] for v in current_year_values], color='green', label='ja')
    ax.bar(current_year_labels, [v['nein'] for v in current_year_values], bottom=[v['ja'] for v in current_year_values], color='red', label='nein')
    ax.set_title(f'Auftreten Schnitzel für das Jahr {datetime.now().year}')
    ax.set_xlabel('Monat')
    ax.set_ylabel('Auftreten')
    ax.legend(title='Auftreten Schnitzel', labels=['ja', 'nein'])
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('webpage/current_year_plot.png')

    # Increase figure size and set dpi for better resolution
    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)  # Adjust figsize and dpi as needed

    # Plot for previous years and save to disk with increased resolution
    ax.bar(previous_years_labels, [v['ja'] for v in previous_years_values], color='green', label='ja')
    ax.bar(previous_years_labels, [v['nein'] for v in previous_years_values], bottom=[v['ja'] for v in previous_years_values], color='red', label='nein')
    ax.set_title('Auftreten Schnitzel für die vergangenen Jahre')
    ax.set_xlabel('Monat')
    ax.set_ylabel('Auftreten')
    ax.legend(title='Auftreten Schnitzel', labels=['ja', 'nein'])
    plt.xticks(rotation=45, ha='right')

     # Adjust font size for x-axis ticks
    plt.xticks(fontsize=6)

    plt.tight_layout()
    plt.savefig('webpage/previous_years_plot.png')


def write_schnitzel_page(answer, stats):
    f = open('webpage/index.html','w') # release
    page_begin = """<!DOCTYPE html>

    <html>

    <head>
    	<meta charset="UTF-8" />
    	<title>Gibt es heute Schnitzel an der Universitaet des Saarlandes?</title>
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

    main_content	= ''.join(["<h1>", answer, "</h1>"])
    statistic		= ''.join(['<h2>', str(stats), '</h2>'])
    link			= ''.join(['<h2>', '<a href="https://mensaar.de/#/menu/sb">Mensaar Speiseplan</a>', '</h2>'])
    fancyPlots		= ''.join(['<h2>', '<a href="evaluation.html">Auswertung</a>', '</h2>'])

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
    f.write(fancyPlots)
    f.write(page_end)
    f.close()


def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


if __name__ == '__main__':
    config = load_config('config.json')
    api_url_baseData = config['api_url_baseData']
    api_url_menu = config['api_url_menu']
    api_key = config['api_key']

    answer, data, isToday = get_schnitzel(api_url_menu, api_key)
    update_stats_file(answer, data, isToday)
    stats, answer = calculate_p_schnitzel()
    write_schnitzel_page(answer, stats)
    # makeFancyPlots()
