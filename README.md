# DT2enex.py
This is pretty rudimentary, but it now successfully runs against a hierarchy of DT html export folders and returns an enex file that Joplin successfully parses and imports. The result is pretty ugly, but it works. Huzzah!

usage: `$python3 DT2enex.py <directory of DT html files with associated resources> <outfile.enex>`

#ToDo:
1. try/except loops for sanity checks on available files, test the base64 encoding
2. check incoming html against list of disallowed elements or attributes.
3. See if we can replace any `<a href="evernote:///view..."`s with URLs that Joplin can make something of: ie. references to other notes (like this? joplin://368595dd912d48ccac5671a8d1ccc365 but, how to derive the hash?)
4. investigate how I might get tags out of the DT and into the html export.
5. So far this works only on DT notes exported as html files with their associated resources; further, so far it only works on `<img>` resources
