#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------[__doc__]----------------------------------#
"""paymybill table scrape
"""
#------------------------------------------------------------------------------#

#-----------------------------------[Imports]----------------------------------#
from __future__ import print_function
import sqlite3
import os
import sys
import argparse
import requests
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
#------------------------------------------------------------------------------#

#---------------------------------[Definitions]--------------------------------#
uri = "https://paymybill.restaurant/fb/restaurant/5739/565/7810/"
#------------------------------------------------------------------------------#

#----------------------------------[Functions]---------------------------------#
def parse_html(raw_input):
    return BeautifulSoup(raw_input, 'lxml')

def update_cookies():
    path = "/home/kr-b/.mozilla/firefox/17lqfjb9.default/cookies.sqlite"
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("SELECT value from moz_cookies where host='paymybill.restaurant'")
    csid = c.fetchall()[0][0]
    return csid

def get_bill(table):
    # Perform web request
    cookie = {"connect.sid": update_cookies()}
    r = requests.get(uri + str(table), cookies=cookie)
    if r.status_code != 200:
        print("Request error %s" % r.status_code)
        exit(1)


    html_raw = r.content.replace('\t','').replace('\n',' ') # Output from web request
    if (html_raw.find("Sorry") != -1):
        return False, False

    html_parsed = parse_html(html_raw)

    # Check if table is empty

    # Extract items from html
    html_ul = html_parsed.findAll("li",{"class": "bill__item"})
    counter = 0
    items = []

    for li in html_ul:
        li = li.text
        if (li[1].isdigit()):
            quantity = int(li.split(' ')[1])
            item = ' '.join(li.split(' ')[2:-2])
            price = float(li.split(' ')[-2][1:]) / quantity
            for x in range(quantity):
                items.append([item,price])

    # items   # [[item, price], ..]
    bill = [] # [[item, quantity, total_cost], ..]

    for item in items:
        item_exists = False
        for x in bill:
            if item[0] in x:
                # Item exists in bill, increment quantity
                x[1] += 1
                x[2] += item[1]
                item_exists = True
                break

        if not item_exists:
            bill.append([item[0], 1, item[1]])

    total = html_parsed.findAll("p",{"class": "bill__tax-line"})[2].text.split(' ')[3][1:]

    return bill, total


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--outfile', help="Output file", default=sys.stdout, type=argparse.FileType('w'))
    args = parser.parse_args(arguments)

    tables = [] # [[table, bill, total], ..]

    for table in range(1,36):
        print("# Fetching table %d" % table)
        bill, total = get_bill(table)
        if (bill == False or total == 0):
            print("# - Empty")
            continue
        print("# Found %d items" % len(bill))
        tables.append([table, bill, total])

    for table in tables:
        print("# ----\tTable %d\t---- #" % table[0])
        for item in table[1]:
            if item[2] == 0:
                print(u"# %d x %s" % (item[1], item[0]))
            else:
                print(u"# %d x %s\t£%s" % (item[1], item[0], item[2]))
        print(u"# ----\t£%s\t---- #\n" % table[2])

#------------------------------------------------------------------------------#

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
