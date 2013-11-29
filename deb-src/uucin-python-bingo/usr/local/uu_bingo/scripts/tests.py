#encoding:utf-8
import getopt
import xapian
from bingo.parser import POI_PARSER

database_path = "/home/duanhongyi/Source/bingo_database/release"
database = xapian.WritableDatabase(database_path, xapian.DB_CREATE_OR_OPEN)
query = POI_PARSER.parse_query(u"pn:鸡味")
enquire = xapian.Enquire(database)
enquire.set_query(query)
matches = enquire.get_mset(0, 1000000, 10000000)
for matche in matches:
    #print(dir(matche.document))
    matche.document.add_posting(0,"PN鸡")
    matche.document.add_posting(1,"PN味")
    database.replace_document(matche.document.get_docid(),matche.document)
    #print(' '.join([term.term for term in matche.document.termlist()]))
database.commit()
