import requests
from BeautifulSoup import BeautifulSoup
from flask import Flask, send_file, abort, render_template
from app import app
import json
import os
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_STATIC = os.path.join(APP_ROOT, 'static')


@app.route('/')
def index():
    page = requests.get('http://www.asx.com.au/asx/markets/equityPrices.do?by=asxCodes&asxCodes=ppl')
    tree = page.text
    soup = BeautifulSoup(''.join(tree))
    table = soup.findAll('table')[1]
    trs = table.findAll('tr')

    tds_headers = trs[0].findAll('th')
    tds_values = trs[1].findAll(['th', 'td'])
    si = len(tds_values)
    data = {}

    for td in range(0, si):
        header = str(tds_headers[td].string) if td == 15 else str(tds_headers[td].find('a').string)
        value = ""
        values = []

        if td in [0, 10, 11, 12, 13, 15]:
            value = str(tds_values[td].find('a').string).rstrip('\r\n\t')
            values = [value, "http://www.asx.com.au" + str(tds_values[td].find('a')['href']).rstrip('\r\n\t')]
        else:
            values = str(tds_values[td].string).rstrip('\r\n\t')

        data[header] = values

    data['date'] = datetime.datetime.now().strftime("%d-%B-%Y %I:%M:%S")
    data['Announcements'] = get_announcement_details()
    data['movement'] = "0"
    data['marketcap'] = "0"

    write_on_file(data)
    return json.dumps(data)


#@app.route('/announcement')
def get_announcement_details():
    driver = webdriver.Firefox()
    driver.get("http://search.asx.com.au/s/search.html?query=ppl&collection=asx-meta&profile=web")
    page_source = driver.page_source

    soup = BeautifulSoup(page_source)
    table = soup.findAll('table', attrs={'class': 'search-results-announcement grid-generic'})
    trs = table[0].findAll('tr')
    announcements = []
    announcement = {}

    for tr in trs:
        tds = tr.findAll('td')

        a = tds[0].find('a')
        announcement['date'] = [str(a.string).strip('\r\n\t'), str(a['href']).strip('\r\n\t')]

        a = tds[2].find('a')
        announcement['headline'] = [str(a.string).strip('\r\n\t'), str(a['href']).strip('\r\n\t')]

        a = tds[4].find('a')
        announcement['pdf'] = [str(a.string).strip('\r\n\t'), str(a['href']).strip('\r\n\t')]

        announcements.append(announcement)

    driver.close()
    #return json.dumps(announcements)
    return announcements


@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def dir_listing(req_path):
    BASE_DIR = ''

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path)

    # # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    files = os.listdir(abs_path)

    return render_template('files.html', files=files)


def write_on_file(data):
    write_data = open("app/static/sharedata.json", "w")
    write_data.write(json.dumps(data))
    write_data.close()