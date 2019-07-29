from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from orangecontrib.text.corpus import Corpus
from Orange.data.domain import filter_visible
from itertools import chain
from nltk import word_tokenize
import re

class MarkDuplicates(OWWidget):
    name = "Mark Duplicates"
    description = "Mark duplicate text parts in corpus"
    icon = "icons/widget2.svg"
    DATEFIELD = 2
    TEXTFIELD = 3
    want_main_area = False
    phraseFrequencies = {}
    phraseInitialPos = {}
    N = 20

    class Inputs:
        corpus = Input("Corpus", Corpus)

    class Outputs:
        corpus = Output("Corpus", Corpus)

    def resetWidget(self):
        self.corpus = None
        self.phraseFrequencies = {}
        self.phraseInitialPos = {}

    def __init__(self):
        super().__init__()
        self.corpus = None
        self.label = gui.widgetLabel(self.controlArea)
    
    def makeRefId(self,date,i):
        return(date+" "+str(i+1))

    def getDateFromRefId(self,refId):
        return(" ".join(refId.split()[0:2]))
    
    def countPhrases(self,date,message):
        words = message.split()
        inDuplicate = False
        duplicateStarts,duplicateEnds,duplicateRefs = [],[],[]
        for i in range(0,len(words)-self.N):
            phrase = " ".join(words[i:i+self.N])
            if phrase in self.phraseFrequencies:
                self.phraseFrequencies[phrase] += 1
                originalDate = self.getDateFromRefId(self.phraseInitialPos[phrase])
                if not inDuplicate:
                    if originalDate > date:
                        inDuplicate = True
                        duplicateStarts.append(i)
                        duplicateRefs.append(self.phraseInitialPos[phrase])
                    elif originalDate < date:
                        self.phraseInitialPos[phrase] = self.makeRefId(date,i)
            else: 
                self.phraseFrequencies[phrase] = 1
                self.phraseInitialPos[phrase] = self.makeRefId(date,i)
                if inDuplicate:
                    inDuplicate = False
                    duplicateEnds.append(i+self.N-2)
        if inDuplicate: duplicateEnds.append(len(words)-1)
        return(duplicateStarts,duplicateEnds,duplicateRefs)

    def markDuplicates(self,message,duplicateStarts,duplicateEnds,duplicateRefs):
        words = message.split()
        outText = ""
        wordIndex = 0
        while len(duplicateStarts) > 0:
            indexDuplicateStarts = duplicateStarts.pop(0)
            indexDuplicateEnds = duplicateEnds.pop(0)
            duplicateRef = duplicateRefs.pop(0)
            if indexDuplicateStarts > wordIndex:
                outText += "<text>"+" ".join(words[wordIndex:indexDuplicateStarts])+"</text>"
            if indexDuplicateStarts < indexDuplicateEnds:
                outText += '<mark data-markjs="true">'+" ".join(words[indexDuplicateStarts:indexDuplicateEnds+1])+"</mark>"
            wordIndex = indexDuplicateEnds+1
        if wordIndex < len(words):
            outText += "<text>"+" ".join(words[wordIndex:])+"</text>"
        return(outText)

    @Inputs.corpus
    def inputAnalysis(self, corpus):
        self.resetWidget()
        self.corpus = corpus
        if self.corpus is None:
            self.label.setText("No corpus available")
        else:
            text = ""
            for row in self.corpus:
                date = str(row[self.DATEFIELD])
                text = str(row.metas[self.TEXTFIELD])
                text = re.sub("</*line>"," ",text)
                text = re.sub(">>+"," ",text)
                text = " ".join(word_tokenize(text))
                duplicateStarts,duplicateEnds,duplicateRefs = self.countPhrases(date,text)
                row.metas[self.TEXTFIELD] = self.markDuplicates(text,duplicateStarts,duplicateEnds,duplicateRefs)
        self.Outputs.corpus.send(self.corpus)
