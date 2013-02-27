import logging, re, sys, pubAlg, util
import unidecode  # to map spec characters to ASCII text (ucsc browser doesn't support unicode)
from pubAlg import *
import maxTables
""" 

"""

class UnifyAuthors:
    """ 
    map-reduce algorithm to map each article to a unique identifier
    that looks like Smith2009ab

    the mapper returns Smith2009 and the list of articleIds
    the reducer appends "a", "b", "c" to the authorYear and yields (articleId, authorYearLetters)

    if paramDict contains "batchIds" and "baseDir", reducer will avoid overlaps
    with baseline and all updates before the current one by checking against all older
    authors.tab files in subdirectories of baseDir/batches
    """
    def __init__(self):
        self.headers = ["articleId", "authorUniqueName"]
        self.runOn = "articles"

    def startup(self, paramDict, resultDict):
        self.batchIds = None
        self.baseDir  = None
        if "batchIds" in paramDict:
            self.batchIds = paramDict["batchIds"]
            self.baseDir  = paramDict["baseDir"]

    def _readOldIdentifiers(self):
        """ search through baseDir and dirs in <baseDir>/batches/
            and get all already assigned authorId from the
            files authors.tab 

            only batches with step "annot" that don't had the step "identifiers"
            run on them will be processed.
        """
        def readIds(fname):
            if os.path.isfile(fname):
                logging.debug("Reading assigned authorIds from %s" % fname)
                return maxTables.TableParser(fname).column("authorUniqueName")
            else:
                logging.warn("Cannot find %s" % fname)
                return set()

        authorIds = []
        if self.batchIds==None:
            self.oldIds = set()
            return

        baseFname = os.path.join(self.baseDir, "authors.tab")
        self.oldIds = set(readIds(baseFname))
        for batchId in self.batchIds:
            baseFname = os.path.join(self.baseDir, "batches", str(batchId), "authors.tab")
            self.oldIds.update(readIds(baseFname))
        
    def map(self, articleData, fileData, text, result):
        " given the article data, return the first author family name, as ASCII "
        nonLetterRe = re.compile('\W', re.U) # non-alphanumeric character in unicode set, uff.
        firstAuthor=articleData.authors.split(";")[0].split(",")[0].replace(" ","")
        assert(type(firstAuthor)==types.UnicodeType)
        if firstAuthor=="":
            #firstAuthor=articleData.externalId
            firstAuthor="NoAuthor"
        else:
            # test if this works with pmcid 1936429
            firstAuthor = nonLetterRe.sub("", firstAuthor) # remove nonalphanumeric characters
            firstAuthor = unidecode.unidecode(firstAuthor) # remove accents

        authorYear = firstAuthor+str(articleData.year)
        articleId  = articleData.articleId
        #self.authorYearIds.setdefault(authorYear, []).append(articleId)
        result.setdefault(authorYear, []).append(articleId)

    def _checkAgainstOld(self, uniqueId):
        """ makes sure that ID is really unique by checking against 
            self.oldIds, return a free id if uniqueId is already taken
        """
        if self.batchIds==None:
            return uniqueId
        if uniqueId not in self.oldIds:
            return uniqueId
        else:
            lastLetter = uniqueId[-1]
            if lastLetter in ["0","1","2","3","4","5","6","7","8","9"]:
                return self._checkAgainstOld(uniqueId+"a")
            elif lastLetter=="z":
                return self._checkAgainstOld(uniqueId[:-1]+"A")
            elif lastLetter=="Z":
                return self._checkAgainstOld(uniqueId+"a")
            else:
                nextLetter = chr(ord(lastLetter)+1)
                return self._checkAgainstOld(uniqueId[:-1]+nextLetter)
            
    def reduceStartup(self, resultDict, paramDict):
        " this is called once before the reduce step "
        self._readOldIdentifiers()

    def reduce(self, authorYear, valList):
        #logging.debug("author: %s, articles: %s" % (authorYear, str(valList)))

        articleIds = []
        for listString in valList:
            ids = listString.split(",")
            ids = [int(x) for x in ids]
            articleIds.extend(ids)

        articleIds.sort()
        if len(articleIds)==1:
            yield (articleIds[0], authorYear)
        else:
            for pos, articleId in enumerate(articleIds):
                suffix = util.baseN(pos)
                uniqueId = authorYear+suffix
                uniqueId = self._checkAgainstOld(uniqueId)
                self.oldIds.add(uniqueId)
                yield (articleId, uniqueId)

class GetFileDesc:
    """ 
    map-reduce algorithm to get the description and url of each file
    """
    def __init__(self):
        self.headers = ["fileId", "desc", "url"]
        self.runOn = "files"

    def map(self, articleData, fileData, text, result):
        fileId = fileData.fileId
        desc   = fileData.desc
        url    = fileData.url
        result[fileId] = [(desc, url)]

    def reduce(self, fileId, valList):
        desc, url = valList[0]
        yield (fileId, desc, url)

