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

IDFIELD = "id"
FROMFIELD = "from"
TOFIELD = "to"
SUBJECTFIELD = "subject"
TEXTFIELD = "text"
DATEFIELD = "date"
FILEFIELD = "file"
DELIMITER = "\t"
FIELDNAMES = [IDFIELD,FILEFIELD,FROMFIELD,TOFIELD,DATEFIELD,SUBJECTFIELD,TEXTFIELD]

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
            if textField == "": textField = "<line>"+line+"</line>"
            else: textField += "<line>"+line+"</line>"
        else:
            match = re.search(r"^(From|To|Date|Subject):\s*(.*)$",line)
            if match and match.group(1) == "From": 
                fromField = match.group(2)
                lastHeading = "From"
            elif match and match.group(1) == "To": 
                toField = match.group(2)
                lastHeading = "To"
            elif match and match.group(1) == "Subject": 
                subjectField = match.group(2)
                lastHeading = "Subject"
            elif match and match.group(1) == "Date": 
                dateString = re.sub(r"\s*\([A-Z]*\)\s*$","",match.group(2))
                dateField = datetime.strftime(datetime.strptime(dateString,"%a, %d %b %Y %H:%M:%S %z"),"%Y-%m-%d %H:%M:%S")
                lastHeading = "Date"
            elif re.search("^\s",line):
                if lastHeading == "To": toField += line
            elif line == "": 
                inHeading = False

    if inFileName != "": inFile.close()
    csvwriter.writerow({IDFIELD:counter,FILEFIELD:inFileName,FROMFIELD:fromField,TOFIELD:toField,DATEFIELD:dateField,SUBJECTFIELD:subjectField,TEXTFIELD:textField})

def main(argv):
    csvwriter = csv.DictWriter(sys.stdout,fieldnames=FIELDNAMES,delimiter=DELIMITER)
    csvwriter.writeheader()
    counter = 1
    if len(argv) <= 0: mail2tsv(sys.stdin,csvwriter,counter)
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
