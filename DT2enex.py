#!/usr/bin/python3

import sys, os, base64, hashlib
from bs4 import BeautifulSoup, Tag, Doctype, CData
from lxml import etree
from lxml.etree import CDATA
from PIL import Image

def guess_type(filepath):
    try:
        import magic  # I havn't got python-magic
        return magic.from_file(filepath, mime=True)
    except ImportError:
        import mimetypes
        return mimetypes.guess_type(filepath)[0]

def file_to_base64(filepath):
    import base64
    with open(filepath, 'rb') as f:
        buff = f.read()
        imghash = hashlib.md5(buff).hexdigest()
        encoded_str = base64.encodebytes(buff).decode("utf-8")
    return imghash, encoded_str

def generateCData(htmlIn):
    """
    This returns noteProps, and html soup to be reduced to a CData string.
    Meta-ToDo: Maybe this should be a method in a class with methods to handle different resource types?
    ToDo: This'll work for img tags but we're going to have to make it more general to handle resources other than images.
    ToDo: It'd be good to replace any <a href="evernote:///view..."s with URLs that Joplin can make something of.
    ToDo: remember to strip out disallowed tags and/or attributes.
    ToDo: return title as a string instead of an item in noteProps?
    """
    basepath, htmlfilename = os.path.split(htmlIn.rstrip(os.path.sep))
    #print(htmlfilename)
    soup = BeautifulSoup(open(htmlIn, 'r'), 'xml')

    noteProps = {'note-title': soup.find('title').text}
    for img in soup.find_all("img"):
        # assemble image properties
        img_path = basepath + img['src'][1:]
        pic = Image.open(img_path)
        width,height = pic.size
        imghash,base64block = file_to_base64(img_path)
        mimetype = guess_type(img_path)

        # make <en-media/> tag and replace img tag with it
        enmedia = Tag(name="en-media", attrs={'hash': imghash, 'type': mimetype})
        img.replaceWith(enmedia)
        
        # generate entry in noteProps
        noteProps[imghash] = {
            'filename': img['src'][2:],
            'path': img_path,
            'type': mimetype,
            'width': str(width),
            'height': str(height),
            'data': base64block
        }

    # ToDo: more soup tinkering to create the CData string
    for t in soup: # do I need this loop?
        if isinstance(t, Doctype):
            t.replaceWith(Doctype('en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"'))
    soup.html.unwrap()
    soup.head.decompose()
    soup.body.name = "en-note"

    return soup, noteProps


def generateNoteElement(html,enex):
    soup, noteProps = generateCData(html)
    note = etree.SubElement(enex, "note")
    title = etree.SubElement(note, 'title').text = noteProps['note-title']
    content = etree.SubElement(note, "content").text = CDATA(str(soup))
    etree.SubElement(note, "created").text = "20161113T034919Z" #todo: replace dummy datetimes
    etree.SubElement(note, "updated").text = "20170725T213730Z"
    nattrs = etree.SubElement(note, "note-attributes")
    etree.SubElement(nattrs, 'author').text = "Jon Crump"

    for x in noteProps:
        d = noteProps[x]
        if x != 'note-title':
            resource = etree.SubElement(note, "resource")
            etree.SubElement(resource, "data", encoding="base64").text = d['data']
            etree.SubElement(resource, "mime").text= d['type']
            etree.SubElement(resource, "width").text= d['width']
            etree.SubElement(resource, "height").text= d['height']

            ratt = etree.SubElement(resource, "resource-attributes")
            etree.SubElement(ratt, 'file-name').text = d['filename']
   

########## wrap the code below in main():

# Creat the .enex xml file. Each note derived from an html file will be added to it
enex = etree.Element("en-export", {"export-date":"20190731T001813Z", "application": "Devonthink"})

for root, dirs, files in os.walk("DTFolders"):
    # exclude hidden files
    files = [f for f in files if not f[0] == '.']
    #dirs[:] is a nice trick to prevent recursion into hidden directories
    dirs[:] = [d for d in dirs if not d[0] == '.']
    
    for file in files:
        if file.endswith("html"):
             generateNoteElement(F"{root + os.path.sep + file}", enex)
             # Python3 string formatting!!

with open("/home/jjon/Projects/DT2enex/bigtest.enex", 'w+') as testfile:
    testfile.write(etree.tostring(enex,
        xml_declaration=True, 
        encoding="UTF-8", 
        doctype='<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">', 
        pretty_print=False).decode("utf-8"))
