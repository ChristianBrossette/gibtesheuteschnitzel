# Copyright 2024 by Christian Brossette
__author__ = "Christian Brossette"
__copyright__ = "Copyright 2024"
__credits__ = ["Christian Brossette"]
__license__ = "GPL"
__version__ = "0.4"
__maintainer__ = "Christian Brossette"
__email__ = "info@gibtesheuteschnitzel.de"
__status__ = ""

import re
import urllib
import urllib.request
import time
import feedparser
import argparse
from datetime import datetime
from collections import defaultdict


parser = argparse.ArgumentParser(description='Schnitzel Page')
args = parser.parse_args()


german_days = {'Mon': 'Montag',
				'Tue': 'Dienstag',
				'Wed': 'Mittwoch',
				'Thu': 'Donnerstag',
				'Fri': 'Freitag',
				'Sat': 'Samstag',
				'Sun': 'Sonntag'}
today = german_days[time.strftime("%a")]


def isMensaOpen():
    with urllib.request.urlopen("http://www.studentenwerk-saarland.de/_menuAtom/1") as url:
        page = url.read()
        d = feedparser.parse(page)
        content_day = str(d.entries[0]['title'].split(',')[0])
        today = time.strftime("%a")

    return content_day == german_days[today]


def get_schnitzel():
    with urllib.request.urlopen("http://www.studentenwerk-saarland.de/_menuAtom/1") as url:
        page = url.read()
        d = feedparser.parse(page)
        # TODO is the first entry always the current day?
        content = str(d.entries[0])
        schnitzel = re.findall(r"Schnitzel|schnitzel", content)

        answer = 'nein'
        if schnitzel and isMensaOpen():
            answer = 'ja'

        return answer


def update_stats_file(answer):

    f = open('stats.txt', 'r+')
    # get the last entry of the stat file
    last_line = None
    for line in f:
        last_line = line

    today_date = time.strftime("%x")

    if isMensaOpen():
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
        else:
            f.write(str(today_date + '_' + answer + '\n'))
        f.close()


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


if __name__ == '__main__':
    answer = get_schnitzel()
    update_stats_file(answer)
    stats, answer = calculate_p_schnitzel()
    write_schnitzel_page(answer, stats)
