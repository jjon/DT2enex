#!/usr/bin/python3

import sys
import os
import base64
from bs4 import BeautifulSoup, Tag, Doctype, CData
from lxml import etree
from lxml.etree import CDATA
from PIL import Image
import hashlib
from pprint import pprint


# "/home/jjon/Projects/DT2enex/B minor/Molly McAlpin - Carolan's Dream.html"
html = "/home/jjon/Projects/DT2enex/Popper/Karl Popper By Philip Catton, Graham Macdonald.html"
# "/home/jjon/Projects/DT2enex/Popper/Karl Popper.html"
#"/home/jjon/Projects/DT2enex/DTTestOut/Edor/Swallowtail.html"


def guess_type(filepath):
    try:
        import magic  # python-magic
        return magic.from_file(filepath, mime=True)
    except ImportError:
        import mimetypes
        return mimetypes.guess_type(filepath)[0]

def file_to_base64(filepath):
    """
    go back to old version returning only the base64 block. Get the imghash in generateCData 
    """
    import base64
    with open(filepath, 'rb') as f:
        buff = f.read()
        imghash = hashlib.md5(buff).hexdigest()
        encoded_str = base64.encodebytes(buff).decode("utf-8")
    return imghash, encoded_str

def generateCData(htmlIn):
    """
    This should return noteProps and a CDATA string.
    Meta-ToDo: Maybe this should be a method in a class with methods to handle different resource types?
    ToDo: This'll work for img tags but we're going to have to make it more general to handle resources other than images.
    ToDo: It'd be good to replace any <a href="evernote:///view..."s with URLs that Joplin can make something of.
    ToDo: remember to strip out disallowed tags and/or attributes.
    """
    basepath, htmlfilename = os.path.split(htmlIn.rstrip(os.path.sep))
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
    for t in soup:
        if isinstance(t, Doctype):
            t.replaceWith(Doctype('en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"'))
    soup.html.unwrap()
    soup.head.decompose()
    soup.body.name = "en-note"

    return soup, noteProps


enex = etree.Element("en-export", {"export-date":"20190731T001813Z", "application": "Devonthink"})

def generateNoteElement(html,enex):
    """
    ToDo: create enex xml and insert CData string
    """
    soup, noteProps = generateCData(html)
    
    note = etree.SubElement(enex, "note")
    title = etree.SubElement(note, 'title').text = noteProps['note-title']
    content = etree.SubElement(note, "content").text = CDATA(str(soup))
    etree.SubElement(note, "created").text = "20161113T034919Z"
    etree.SubElement(note, "updated").text = "20170725T213730Z"
    natt = etree.SubElement(note, "note-attributes")
    etree.SubElement(natt, 'author').text = "Jon Crump"

    for x in noteProps:
        if x != 'note-title':
            d = noteProps[x]
            resource = etree.SubElement(note, "resource")
            etree.SubElement(resource, "data", encoding="base64").text = d['data']
            etree.SubElement(resource, "mime").text= d['type']
            etree.SubElement(resource, "width").text= d['width']
            etree.SubElement(resource, "height").text= d['height']

            ratt = etree.SubElement(resource, "resource-attributes")
            etree.SubElement(ratt, 'file-name').text = d['filename']
   
generateNoteElement(html,enex)

with open("/home/jjon/Projects/DT2enex/testfile.enex", 'w+') as testfile:
    testfile.write(etree.tostring(enex, xml_declaration=True, encoding="UTF-8", doctype='<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">', pretty_print=False).decode("utf-8"))


#print(etree.tostring(enex, xml_declaration=True, encoding="UTF-8", doctype='<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">', pretty_print=False))
#print(generateEnex(html))