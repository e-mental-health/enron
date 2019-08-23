from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from orangecontrib.text.corpus import Corpus
from Orange.data.domain import filter_visible
from itertools import chain
from nltk import word_tokenize
import re
import numpy as np

class MarkDuplicates(OWWidget):
    name = "Mark Duplicates"
    description = "Mark duplicate text parts in corpus"
    icon = "icons/MarkDuplicates.svg"
    N = 20
    FIELDNAMEDATE = "date"
    FIELDNAMETEXT = "text"
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
        return(date+" "+str(i+1))

    def getDateFromRefId(self,refId):
        return(" ".join(refId.split()[0:2]))
    
    def makePhrase(self,wordList,index):
        return(" ".join(wordList[index:index+self.N]))

    def addPhraseToRefs(self,phrase,date,index):
        self.phraseRefs[phrase] = self.makeRefId(date,index)

    def updatePhraseInRefs(self,phrase,date,index):
        originalDate = self.getDateFromRefId(self.phraseRefs[phrase])
        if originalDate < date:
            self.phraseRefs[phrase] = self.makeRefId(date,index)

    def countPhrases(self,date,message):
        words = message.split()
        inDuplicate = False
        duplicateStartRefEnds = []
        for i in range(0,len(words)-self.N):
            phrase = self.makePhrase(words,i)
            if not phrase in self.phraseRefs:
                self.addPhraseToRefs(phrase,date,i)
                if inDuplicate:
                    inDuplicate = False
                    duplicateStartRefEnds[-1].append(i+self.N)
            else:
                self.updatePhraseInRefs(phrase,date,i)
                originalDate = self.getDateFromRefId(self.phraseRefs[phrase])
                if not inDuplicate and originalDate > date:
                    inDuplicate = True
                    duplicateStartRefEnds.append([i,self.phraseRefs[phrase]])
        if inDuplicate: duplicateStartRefEnds[-1].append(len(words))
        return(duplicateStartRefEnds)

    def markDuplicates(self,message,duplicateStartRefEnds):
        words = message.split()
        outText = ""
        wordIndex = 0
        while len(duplicateStartRefEnds) > 0:
            indexDuplicateStarts,duplicateRef,indexDuplicateEnds = duplicateStartRefEnds.pop(0)
            if indexDuplicateStarts > wordIndex:
                outText += "<text>"+" ".join(words[wordIndex:indexDuplicateStarts])+"</text>"
            if indexDuplicateStarts < indexDuplicateEnds:
                outText += '<mark data-markjs="true">'+" ".join(words[indexDuplicateStarts:indexDuplicateEnds])+"</mark>"
            wordIndex = indexDuplicateEnds
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
        duplicateStartRefEndsArray = []
        if self.corpus is None:
            self.label.setText("No corpus available")
        else:
            text = ""
            self.fieldIdDate = self.getFieldId(self.corpus,self.FIELDNAMEDATE)
            self.fieldIdText = self.getFieldId(self.corpus,self.FIELDNAMETEXT)
            for i in range(0,len(self.corpus.metas)):
                date = str(self.corpus.metas[i][self.fieldIdDate])
                text = self.prepareText(str(self.corpus.metas[i][self.fieldIdText]))
                duplicateStartRefEnds = self.countPhrases(date,text)
                np.append(self.corpus.metas[i],[str(duplicateStartRefEnds)])
                duplicateStartRefEndsArray.append([str(duplicateStartRefEnds)])
                self.corpus.metas[i][self.fieldIdText] = self.markDuplicates(text,duplicateStartRefEnds)
                OWWidget.progressBarSet(self,100*(i+1)/len(self.corpus.metas))
        # np.append(self.corpus.metas,np.array(duplicateStartRefEndsArray),axis=1) 
        self.Outputs.corpus.send(self.corpus)
        self.label.setText(str(self.corpus.metas[53]))
