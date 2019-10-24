#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, re, string, urllib
reload(sys)
sys.setdefaultencoding('utf-8')
from bs4 import BeautifulSoup as bs
#import traceback
from os import path
#from selenium import webdriver
#from time import time
#from random import shuffle
import json
from collections import Counter
import lxml.etree
import lxml.builder
from HTMLParser import HTMLParser
from string import digits
from string import punctuation


from bs4 import BeautifulStoneSoup as bss
import cgi

def load_url(a_url):
	filehandle = urllib.urlopen(a_url, proxies={}).read()
	return filehandle

def load_html(infile):
    html = open(infile, 'rb').read()
    return html 

def get_anti_links(html):
	tuples = []
	soup = bs(html, "lxml")
	uebersicht = soup.find("div", {"id" : "uebersicht_box"}).find_all("a")
	for a in uebersicht:
		a_link = a['href']
		a_text = a.text
		tuples.append([a_text, a_link])

	return tuples

def get_meta_data(html):
    soup = bs(html, "lxml")
    tab_content = soup.find("div", {"class" : "tab-content"})
    a_title = tab_content.find("h2")
    a_info = tab_content.find_all("h4")
    title, year, genre = extract_title(a_title)
    info = {}
    info['Titel'] = title
    info['Jahr'] = year
    info['Genre'] = genre
    for h4 in a_info:
        key = h4.text
        key = key.strip()
        if key == 'Epochen':
            key = 'Epoche'
        
        value = h4.next_sibling.replace(":", "")
        value = value.strip()
        value = value.rstrip(',')

        if key == "Epoche":
            value = handle_epoche(value)

        info[key] = value
    return info

def handle_epoche(value):
    if value == "Weimarer Klassik":
        return [u'Weimarer Klassik']
    newvalue = []
    if "/" in value:
        value = value.split("/")
    elif len(value.split()) > 4:
        pass
    else:
        value = value.split()
    for i in value:
        i = i.rstrip(',')
        i = i.strip()
        newvalue.append(i)
    return newvalue

def get_poem_data(html):
    pattern = re.compile(r"\d*([^\d\W]+)\d*")
    htmlparser = HTMLParser()
    soup = bs(html, "lxml")
    table = soup.find("table", {"class" : "noborder"})
    tds = table.find_all("td")
    poem = {}
    stanza = []
    stanza_no = 0
    for td in tds:
        txt1 = htmlparser.unescape(td.text)
        txt = pattern.sub(r"\1", txt1)
        txt = txt.strip()
        attr_class = ''
        try:
            attr_class = td['class']
        except KeyError:
            pass
        if "strophenbinder_top" in attr_class:
            if stanza_no < 1:
                stanza_no += 1
                continue
            else:
                poem[stanza_no] = stanza
                stanza = []
                stanza_no += 1
                continue
        elif len(txt) > 1:
            stanza.append(txt)
        if td is tds[-1]:
            poem[stanza_no] = stanza
        else:
            continue
    return poem


def make_tei(info, poem):
    print info
    print poem
    no_verses = len(poem.keys())
    print no_verses
    """
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title>Review: an electronic transcription</title>
                    <author>
                        <persName>
                            <name>Max Mustermann</name>
                        </persName>
                    </author>
                </titleStmt>
                <extent>
                    <measure type="images">120</measure>
                    <measure type="tokens">24309</measure>
                    <measure type="types">6073</measure>
                    <measure type="characters">154104</measure>
                </extent>
                <publicationStmt>
                    <p>Published as an example for the Introduction module of TBE.</p>
                </publicationStmt>
                <sourceDesc>
                    <p>No source: born digital.</p>
                </sourceDesc>
            </fileDesc>
        </teiHeader>
        <text>
            <body>
                <head>Review</head>
                <p>
                    <title>Die Leiden des jungen Werther</title>
                    <note place="foot">by <name>Goethe</name></note>
                is an
                    <emph>exceptionally</emph>
                    good example of a book full of <term>Weltschmerz</term>.</p>
            </body>
        </text>
    </TEI>
    """
    tei_namespace = "http://www.tei-c.org/ns/1.0"
    tei_nsmap = {None: tei_namespace}
    E = lxml.builder.ElementMaker(namespace=tei_namespace, nsmap=tei_nsmap)
    TEI = E.TEI
    teiHeader = E.teiHeader
    fileDesc = E.fileDesc
    titleStmt = E.titleStmt
    title = E.title
    author = E.author
    publicationStmt = E.publicationStmt
    publisher = E.publisher
    pubPlace = E.pubPlace
    date = E.date
    sourceDesc = E.sourceDesc
    editor = E.editor
    persName = E.persName
    name = E.name
    surname = E.surname
    forename = E.forename

    editionStmt = E.editionStmt
    edition = E.edition
    email = E.email
    orgName = E.orgName
    extent = E.extent
    measure = E.measure

    profileDesc = E.profileDesc
    textClass = E.textClass
    classCode = E.classCode  # For literary period / epoch
    term = E.term

    text = E.text
    body = E.body
    div = E.div
    lg = E.lg
    head = E.head
    l = E.l
    p = E.p

    titel = info['Titel']
    autor = info['Autor']
    vorname, nachname = get_forename_surname(autor)
    genre = info['Genre']
    jahr = info['Jahr']
    epochen = info['Epoche']

    strophen = info['Strophen']
    verse = info['Verse']
    saetze = info[u'Sätze']
    woerter = info[u'Wörter']
    verse_pro_strophe = info['Verse pro Strophe']
    buchstaben = info['Buchstaben']

    link = info['Link']
    link_text = info['LinkText']

    the_doc = TEI(
        teiHeader(
            fileDesc(
                titleStmt(
                    title(titel, TYPE('main')),
                    author(
                        persName(
                            surname(nachname),
                            forename(vorname)
                        )
                    ),
                    editor(
                        persName(
                            surname('Haider'),
                            forename('Thomas Nikolaus')
                        ),
                        orgName('Max Planck Institute for Empirical Aesthetics, Frankfurt am Main'),
                        email('thomas.haider@ae.mpg.de')
                    )
                ),
                editionStmt(
                    edition(
                            name('Deutscher Lyrik Korpus Edition (DLK)'),
                            date('1-11-2017'),
                    )
                ),
                extent(
                    measure(strophen, TYPE('stanzas')),
                    measure(verse, TYPE('verses')),
                    measure(verse_pro_strophe, TYPE('verses_per_stanza')),
                    measure(woerter, TYPE('tokens')),
                    measure(saetze, TYPE('sentences')),
                    measure(buchstaben, TYPE('characters'))
                ),
                publicationStmt(
                    publisher(
                        name()
                    ),
                    pubPlace(),
                    date(jahr, TYPE('publication'))
                ),
                sourceDesc(
                    p(link_text, corresp=link),
                )
            ),
            profileDesc(
                textClass(
                    classCode(
                        *make_epochen(epochen, term),
                        scheme='literary_period'
                    ),
                    classCode(
                        genre,
                        scheme='text_genre'
                    )
                )
            )
        ),
        text(
            body(
                div(N('1'),
                    lg(TYPE('poem'),
                       head(titel),
                       *[lg(TYPE('stanza'), rhyme='None',
                            *[
                                l("%s" % (poem[row_num + 1][col_num])) for col_num in range(len(poem[row_num + 1]))
                                ]
                            ) for row_num in range(int(no_verses))
                         ]
                       )
                    )
            )
        )
    )

    # the_doc = ROOT(
    #        DOC(
    #            FIELD1('some value1', name='blah'),
    #            FIELD2('some value2', name='asdfasd'),
    #            )
    #        )

    return the_doc

def get_forename_surname(name):
    a_split = name.split()
    surname = a_split[-1].strip()
    forename = " ".join(a_split[:-1]).strip()
    return forename, surname

def make_epochen(epochen, term):
    result = list()
    for epoche in epochen:
        result.append(epoche)
    return result

def N(*args):
	return {"n":' '.join(args)}

def RHYME(*args):
	return {"rhyme":' '.join(args)}

def TYPE(*args):
	return {"type":' '.join(args)}

def IDNO(*args):
	return {"idno":' '.join(args)}

def html2unicode(text):
    """Converts HTML entities to unicode.  For example '&amp;' becomes '&'."""
    text = unicode(bss(text, convertEntities=bss.ALL_ENTITIES))
    return text

def unicode2html(text):
    """Converts unicode to HTML entities.  For example '&' becomes '&amp;'."""
    text = cgi.escape(text).encode('ascii', 'xmlcharrefreplace')
    return text

def extract_title(node):
    a = node.find("a")
    title = a.text
    year_info = a.next_sibling
    year = re.search(r".*(\d{4}).*", year_info).group(1)
    genre = a.previous_sibling
    table = string.maketrans("","")
    genre = genre.translate(digits)
    genre = genre.translate(punctuation)
    genre = genre.strip()
    genre = genre.rstrip(":")
    return title, year, genre

def write_to_file(outpath, info, the_doc):
    htmlparser = HTMLParser()
    author = info['Autor'].replace("/", "")
    title = info['Titel'].replace("/", "")
    year = info['Jahr'].replace("/", "")

    filename = year + "_" + "_".join(title.split()) + "_" + "_".join(author.split()) + ".xml"
    filepath = os.path.join(outpath, filename)

    outfile = open(filepath, 'wb')

    outfile.write(htmlparser.unescape(lxml.etree.tostring(the_doc, pretty_print=True)))



def go(uebersicht_path, store_path, debug=False):
    print "Loading Links"
    print

    nav_site = load_html(uebersicht_path)
    text_links = get_anti_links(nav_site)
    all_counted = len(text_links)
    counter = 0
    actual = 0
    history = {}

    if debug == True:
        text_links = text_links[:10]

    print "-----------------------------"
    print "Getting Data from Links"
    print
    for text, link in text_links:
        print "*****************************"
        counter += 1
        print "Actual " + str(actual) + " Text " + str(counter) + " von " + str(all_counted)
        print "-----------------------------"
        print text
        print link
        print "Loading URL"
        html = load_url(link)
        if "Dieses Werk ist urheberrechtlich" in html:
            print "Dieses Werk ist urheberrechtlich geschützt"
            continue
        print "Get META Data"
        info = get_meta_data(html)
        info['Link'] = link
        info['LinkText'] = text
        if not check_meta_data(info):
            continue
        print "Get POEM Data"
        poem = get_poem_data(html)
        is_history, history = in_history(history, info, poem)
        if is_history:
            print "Already in Database"
            continue
        no_characters = count_characters(poem)
        info['Buchstaben'] = no_characters
        print "Making TEI ready"
        the_doc = make_tei(info, poem)
        print "Writing TEI to File"
        write_to_file(store_path, info, the_doc)
        print
        actual += 1


def count_characters(poem):
    total_count = 0
    for no, stanza in poem.items():
        for verse in stanza:
            verse_count = float(len(verse))
            white_count = float(verse.count(' '))
            no_white_count = verse_count - white_count
            total_count += no_white_count
    return str(int(total_count))

def in_history(history, info, poem):
    is_in = False
    author = info['Autor']
    firstline = poem[1][0]

    if author in history.keys():
        if firstline in history[author]:
            is_in = True

    lines = history.setdefault(author, [])
    lines.append(firstline)

    return is_in, history

def check_meta_data(info):
    t_value = True
    genre = info['Genre']
    if "Drama" in genre or "Novelle" in genre:
        print "Dieses Werk ist kein Gedicht"
        t_value = False
    elif "1. " in genre:
        print "Dieses Dokument ist ein Gedichtvergleich"
        t_value = False
    try:
        if info['Strophen']:
            pass
    except KeyError:
        print "Dieses Werk hat keine Strophen"
        t_value = False
    return t_value

if __name__ == "__main__":
	#antikoerperchen_link = "http://lyrik.antikoerperchen.de/uebersicht.html"
	#html = load_url(antikoerperchen_link)
	#go("./uebersicht.html")
    #html = load_html(sys.argv[1])
    #info = get_meta_data(html)
    #poem = get_poem_data(html)
    #the_doc = make_tei(info, poem)
    #write_to_file('./outdir', info, the_doc)
    go(sys.argv[1], sys.argv[2], debug=False)

