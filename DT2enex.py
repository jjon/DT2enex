#!/usr/bin/python3

import sys, os, base64, hashlib
from bs4 import BeautifulSoup, Tag, Doctype, CData
from lxml import etree
from lxml.etree import CDATA
from PIL import Image
from datetime import datetime as dt

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
    etree.SubElement(note, "created").text = f"{dt.utcnow().strftime('%Y%m%dT%H%M%SZ')}" #todo: replace dummy datetimes
    etree.SubElement(note, "updated").text = f"{dt.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
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

            rattrs = etree.SubElement(resource, "resource-attributes")
            etree.SubElement(rattrs, 'file-name').text = d['filename']
   
    
def main(DTFolders, OUTfile):
    # Create the .enex xml file. Each <note> element derived from an html file will be added to it.
    enex = etree.Element(
        "en-export",
        {"export-date":f"{dt.utcnow().strftime('%Y%m%dT%H%M%SZ')}", 
        "application": "Devonthink"}
    )

    for root, dirs, files in os.walk(DTFolders):
        # exclude hidden files
        files = [f for f in files if not f[0] == '.']

        #dirs[:] is a nice trick to prevent recursion into hidden directories: it
        #replaces the *elements* of the list with directory names matching the
        #criteria, not the name for the list.
        dirs[:] = [d for d in dirs if not d[0] == '.']
        
        for file in files:
            if file.endswith("html"):
                 generateNoteElement(f"{root + os.path.sep + file}", enex)
                 # Python3 string formatting!!

    with open(OUTfile, 'w+') as testfile:
        testfile.write(etree.tostring(enex,
            xml_declaration=True, 
            encoding="UTF-8", 
            doctype='<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">', 
            pretty_print=True).decode("utf-8"))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit("usage: $python3 DT2enex.py <directory of DT html files with associated resources> <outfile.enex>")
    else:
        indir = sys.argv[1]
        outfile = sys.argv[2]
        if outfile[-5:] != '.enex':
            outfile = outfile + '.enex'
        main(indir,outfile)
