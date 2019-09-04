
This now successfully runs against a hierarchy of DT html export folders and returns an enex file that Joplin successfully parses and imports. The result is pretty ugly, but it works. Huzzah!

#ToDo:
1. try/except loops for sanity checks on available files, test the base64 encoding
2. check incoming html against list of disallowed elements or attributes.
3. See if we can replace any `<a href="evernote:///view..."`s with URLs that Joplin can make something of: ie. references to other notes (by title?)
4. datetime code to replace dummy date strings
5. sys.argv infrastructure to allow this to be run at the command line
