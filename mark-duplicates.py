#!/usr/bin/env python
# mark-duplicates.py: mark duplicate text in email text
# usage: mark-duplicates.py (in orange3 environment)
# note: assumes input corpus is sorted by date
# 20190726 erikt(at)xs4all.nl

from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from orangecontrib.text.corpus import Corpus
from Orange.data.domain import filter_visible
from itertools import chain
from nltk import word_tokenize
import re
import datetime
import numpy as np

class MarkDuplicates(OWWidget):
    name = "Mark Duplicates"
    description = "Mark duplicate text parts in corpus"
    icon = "icons/MarkDuplicates.svg"
    N = 20
    FIELDNAMEDATE = "date"
    FIELDNAMETEXT = "text"
    FIELDNAMEEXTRA = "extra"
    DATEFORMAT = "%Y-%b-%d %H:%M:%S"
    want_main_area = False

    class Inputs:
        corpus = Input("Corpus", Corpus)

    class Outputs:
        corpus = Output("Corpus", Corpus)

    def resetWidget(self):
        self.corpus = None
        self.phraseRefs = {}

    def __init__(self):
        super().__init__()
        self.label = gui.widgetLabel(self.controlArea)
        self.progress = gui.ProgressBar(self, 100)
        self.resetWidget()
    
    def makeRefId(self,date,i):
        return(date.strftime(self.DATEFORMAT)+" "+str(i+1))

    def getDateFromRefId(self,refId):
        return(" ".join(refId.split()[0:2]))
    
    def makePhrase(self,wordList,index):
        return(" ".join(wordList[index:index+self.N]))

    def addPhraseToRefs(self,phrase,date,index):
        self.phraseRefs[phrase] = self.makeRefId(date,index)

    def updatePhraseInRefs(self,phrase,date,index):
        originalDate = datetime.datetime.strptime(self.getDateFromRefId(self.phraseRefs[phrase]),self.DATEFORMAT)
        if originalDate < date:
            self.phraseRefs[phrase] = self.makeRefId(date,index)

    def countPhrases(self,date,message):
        words = message.split()
        inDuplicate = False
        duplicateRefStartEnds = []
        for i in range(0,len(words)-self.N+1):
            phrase = self.makePhrase(words,i)
            if not phrase in self.phraseRefs:
                self.addPhraseToRefs(phrase,date,i)
                if inDuplicate:
                    inDuplicate = False
                    duplicateEnd = i+self.N
                    duplicateRefStartEnds[-1].append(duplicateEnd)
            else:
                self.updatePhraseInRefs(phrase,date,i)
                if not inDuplicate:
                    inDuplicate = True
                    duplicateSource = self.phraseRefs[phrase]
                    duplicateStart = i
                    duplicateRefStartEnds.append([duplicateSource,duplicateStart])
        if inDuplicate:
            duplicateEnd = len(words)
            duplicateRefStartEnds[-1].append(duplicateEnd)
        return(duplicateRefStartEnds)

    def markDuplicates(self,message,duplicateRefStartEnds):
        words = message.split()
        outText = ""
        wordIndex = 0
        while len(duplicateRefStartEnds) > 0:
            duplicateSource,duplicateStart,duplicateEnd = duplicateRefStartEnds.pop(0)
            if duplicateStart > wordIndex:
                outText += "<text>"+" ".join(words[wordIndex:duplicateStart])+"</text>"
            if duplicateStart < duplicateEnd:
                outText += '<mark data-markjs="true">'+" ".join(words[duplicateStart:duplicateEnd])+"</mark>"
            wordIndex = duplicateEnd
        if wordIndex < len(words):
            outText += "<text>"+" ".join(words[wordIndex:])+"</text>"
        return(outText)

    def prepareText(self,text):
        text = re.sub("</*line>"," ",text)
        text = re.sub(">>+"," ",text)
        text = " ".join(word_tokenize(text))
        return(text)

    def getFieldId(self,corpus,fieldName):
        fieldId = -1
        for i in range(0,len(corpus.domain.metas)):
            if str(corpus.domain.metas[i]) == fieldName:
                fieldId = i
        return(fieldId)

    @Inputs.corpus
    def inputAnalysis(self, corpus):
        self.resetWidget()
        self.corpus = corpus
        OWWidget.progressBarInit(self)
        duplicateRefStartEndsArray = []
        if self.corpus is None:
            self.label.setText("No corpus available")
        else:
            text = ""
            self.fieldIdDate = self.getFieldId(self.corpus,self.FIELDNAMEDATE)
            self.fieldIdText = self.getFieldId(self.corpus,self.FIELDNAMETEXT)
            self.fieldIdExtra = self.getFieldId(self.corpus,self.FIELDNAMEEXTRA)
            for i in range(0,len(self.corpus.metas)):
                date = datetime.datetime.fromtimestamp(self.corpus.metas[i][self.fieldIdDate])
                text = self.prepareText(str(self.corpus.metas[i][self.fieldIdText]))
                duplicateRefStartEnds = self.countPhrases(date,text)
                duplicateRefStartEndsArray.append([list(duplicateRefStartEnds)])
                self.corpus.metas[i][self.fieldIdExtra] = list(duplicateRefStartEnds)
                self.corpus.metas[i][self.fieldIdText] = self.markDuplicates(text,duplicateRefStartEnds)
                OWWidget.progressBarSet(self,100*(i+1)/len(self.corpus.metas))
        # np.append(self.corpus.metas,np.array(duplicateRefStartEndsArray),axis=1) 
        self.Outputs.corpus.send(self.corpus)
