# AppleTree
AppleTree notes taking application.

Early development stage. Nothing to write about ;-)

Many thanks to contributors (testers and feature requests authors ;-) ):

- kooziolm https://github.com/kooziolm
- vojteq https://github.com/vojteq
- casainho https://github.com/casainho

Requirements:
- Python 3
- PyQt5 or PyQt4 (automatic fallback from 5 to 4, not fully tested with 5)

Features (to be implemented before first offcial stable realase):
- (+) Multiple backends support
    - (+) Built-in local backend
    - Encryption for local backend
    - Network document share (push your document to other AppleTree instance in network neighborhood with discovery protocol)
- Different types of documents
    - (+) RichText
    - PlainText with syntax hilighting
- (+) Plugins
    - (+) Screenshot Plugin - allow inserting screenshot directly to the document
- Attachments - allows to add attachments to the document (binary format, any file can be attached)

Features to be implemented in next versions:
- Network storage backends (like WebDav, etc)
- AppleTree Server Backend (centralized repository with ACLs for group work)
- Different types of documents
    - GridData (simple Grid/Table data)
    - Tasks (table-like list with tasks to be done)
- Backup feature
- Import/Export to other AT instance
- Import from other formats (e.g. CherryTree, KeepNote)


![alt text](https://raw.githubusercontent.com/jkolczasty/appletree/master/screenshots/appletree.png)
