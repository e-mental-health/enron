from Orange.widgets.widget import OWWidget, Input
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
    TEXTFIELD = 3
    want_main_area = False
    phraseFrequencies = {}
    phraseInitialPos = {}

    class Inputs:
        corpus = Input("Corpus", Corpus)

    def __init__(self):
        super().__init__()
        self.corpus = None
        self.label = gui.widgetLabel(self.controlArea, "The number is: ??")
    
    def makeRefId(fileName,message,i):
        return(fileName+"."+message.attrib["id"]+"."+str(i+1))
    
    def countPhrases(fileName,message):
        words = message.text.split()
        inDuplicate = False
        duplicateStarts,duplicateEnds,duplicateRefs = [],[],[]
        for i in range(0,len(words)-N):
            phrase = " ".join(words[i:i+N])
            if phrase in self.phraseFrequencies: 
                self.phraseFrequencies[phrase] += 1
                if not inDuplicate:
                    inDuplicate = True
                    duplicateStarts.append(i)
                    duplicateRefs.append(self.phraseInitialPos[phrase])
            else: 
                self.phraseFrequencies[phrase] = 1
                self.phraseInitialPos[phrase] = makeRefId(fileName,message,i)
                if inDuplicate:
                    inDuplicate = False
                    duplicateEnds.append(i+N-2)
        if inDuplicate: duplicateEnds.append(len(words)-1)
        return(duplicateStarts,duplicateEnds,duplicateRefs)

    @Inputs.corpus
    def set_corpus(self, corpus):
        """Set the input corpus."""
        self.corpus = corpus
        if self.corpus is None:
            self.label.setText("No corpus available")
        else:
            for i in range(0,len(self.corpus.metas)):
                text = str(self.corpus.metas[i][self.TEXTFIELD])
                text = re.sub("</*line>","",text)
                text = " ".join(word_tokenize(text))
                self.label.setText(text)
                break
