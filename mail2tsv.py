#!/usr/bin/env python
"""
    mail2tsv.py: convert email file to tsv data for orange3
    usage: mail2tsv.py file1 [file2 ...] > file.tsv
    20190722 erikt(at)xs4all.nl
"""

import csv
from datetime import datetime
import re
import sys
import time

COMMAND = sys.argv[0]
IDFIELD = "id"
FILEFIELD = "file"
FROMFIELD = "from"
TOFIELD = "to"
DATEFIELD = "date"
SUBJECTFIELD = "subject"
TEXTFIELD = "text"
EXTRAFIELD = "extra"
DISCRETEFIELD = "discrete"
STRINGFIELD = "string"
TIMEFIELD = "time"
IGNOREFIELD = "ignore"
METAFIELD = "meta"
USEFIELD = "use=True"
EMPTYSTRING = ""
DELIMITER = "\t"
DATEFORMAT1 = "%a, %d %b %Y %H:%M:%S %z" 
DATEFORMAT2 = "%Y-%m-%d %H:%M:%S"
FIELDNAMES1 = [IDFIELD,FILEFIELD,FROMFIELD,TOFIELD,DATEFIELD,SUBJECTFIELD,TEXTFIELD,EXTRAFIELD]
FIELDNAMES2 = {IDFIELD:DISCRETEFIELD,FILEFIELD:STRINGFIELD,FROMFIELD:STRINGFIELD,TOFIELD:STRINGFIELD,
               DATEFIELD:TIMEFIELD,SUBJECTFIELD:STRINGFIELD,TEXTFIELD:STRINGFIELD,EXTRAFIELD:STRINGFIELD}
FIELDNAMES3 = {IDFIELD:IGNOREFIELD,FILEFIELD:METAFIELD,FROMFIELD:METAFIELD,TOFIELD:METAFIELD,
               DATEFIELD:METAFIELD,SUBJECTFIELD:METAFIELD,TEXTFIELD:USEFIELD,EXTRAFIELD:METAFIELD}

def cleanUpWhiteSpace(line):
    line = re.sub(r"\r",r"",line)
    line = re.sub(r"\n",r"",line)
    line = re.sub(r"\t",r" ",line)
    line = re.sub(r"\s*$","",line)
    return(line)

def mail2tsv(inFileName,csvwriter,counter):
    if inFileName == "": inFile = sys.stdin
    else: inFile = open(inFileName,"r")
    inHeading = True
    lastHeading = ""
    fromField,toField,subjectField,dateField,textField = "","","","",""
    for line in inFile:
        line = cleanUpWhiteSpace(line)
        if not inHeading: 
            textField += "<line>"+line+"</line>"
        else:
            match = re.search(r"^(From|To|Date|Subject):\s*(.*)$",line)
            if match: key,value = match.group(1),match.group(2)
            if match and key == "From": 
                fromField = value
                lastHeading = key
            elif match and key == "To": 
                toField = value
                lastHeading = key
            elif match and key == "Subject": 
                subjectField = value
                lastHeading = key
            elif match and key == "Date": 
                dateString = re.sub(r"\s*\([A-Z]*\)\s*$","",value)
                dateField = datetime.strftime(datetime.strptime(dateString,DATEFORMAT1),DATEFORMAT2)
                lastHeading = key
            elif re.search("^\s",line):
                if lastHeading == "To": toField += line
                elif lastHeading == "Subject": subjectField += line
                elif lastHeading == "From": fromField += line
                else: sys.exit(COMMAND+": problem processing extra line for field "+lastheading+" in file "+inFileName)
            elif line == "": 
                inHeading = False

    if inFileName != "": inFile.close()
    csvwriter.writerow({IDFIELD:counter,FILEFIELD:inFileName,FROMFIELD:fromField,TOFIELD:toField,DATEFIELD:dateField,SUBJECTFIELD:subjectField,TEXTFIELD:textField,EXTRAFIELD:EMPTYSTRING})

def openStdoutAsCsv():
    csvwriter = csv.DictWriter(sys.stdout,fieldnames=FIELDNAMES1,delimiter=DELIMITER)
    csvwriter.writeheader()
    csvwriter.writerow(FIELDNAMES2)
    csvwriter.writerow(FIELDNAMES3)
    return(csvwriter)

def main(argv):
    csvwriter = openStdoutAsCsv()
    counter = 1
    if len(argv) <= 0: 
        mail2tsv(EMPTYSTRING,csvwriter,counter)
    else:
        for inFileName in argv:
            try:
                mail2tsv(inFileName,csvwriter,counter)
                counter += 1
            except Exception as e:
                sys.exit("problem processing file "+inFileName+" "+str(e))
    return(0)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
