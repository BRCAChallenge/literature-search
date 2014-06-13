# some algorithms to run over text files
# -*- coding: iso-8859-15 -*-
# coding=utf-8

# includes functions to load algorithms from external python files,
# run them on pubStores, do map/reduce like algorithms on cluster, etc

# module will call itself on the compute nodes if run on a cluster (->findFileSubmitJobs)

import logging, sys, os, shutil, glob, optparse, copy, types, string, pipes, gzip, \
    doctest, marshal, random

from os.path import *
from maxCommon import *

import pubGeneric, maxRun, pubConf, pubStore, pubAlg, maxCommon

# make sure that sys.stdout uses utf8
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# extension of map output files
MAPREDUCEEXT = ".marshal.gz"

def loadClass(aMod, className, quiet=False):
    " try to find class in a module and return it if found, otherwise None "
    logging.debug("trying to load class %s" % className)
    if className==None:
        return None
    if not hasattr(aMod, className):
        if not quiet:
            logging.debug("Could not find class %s " % (className))
        return None
    else:
        ClassObj = getattr(aMod, className)
        alg   = ClassObj()
        logging.debug("Instantiated class %s in module" % className)
        return alg

def loadPythonObject(moduleFilename, className, defClass=None):
    """ get function or object from dynamically loaded .py file """
    # must add path to system search path first
    #if not os.path.isfile(moduleFilename):
        #moduleFilename = join(pubConf.scriptDir, moduleFilename)
    if not os.path.isfile(moduleFilename):
        moduleFilename = join(dirname(__file__), "..", "scripts", moduleFilename)

    if not os.path.isfile(moduleFilename):
        logging.error("Could not find %s" % moduleFilename)
        sys.exit(1)
    modulePath, moduleName = os.path.split(moduleFilename)
    moduleName = moduleName.replace(".py","")
    logging.debug("Loading python code from %s (class %s, default class %s)" % (moduleFilename, className, defClass))
    sys.path.append(modulePath)

    # load algMod as a module, copied from 
    # http://code.activestate.com/recipes/223972-import-package-modules-at-runtime/
    try:
        aMod = sys.modules[moduleName]
        if not isinstance(aMod, types.ModuleType):
            raise KeyError
    except KeyError:
        # The last [''] is very important!
        aMod = __import__(moduleName, globals(), locals(), [''])
        sys.modules[moduleName] = aMod

    # first try className, then default class, then module itself
    alg = loadClass(aMod, className, quiet=True)
    if alg==None:
        alg = loadClass(aMod, defClass)
    if alg==None:
        return aMod
    else:
        return alg

def getAlg(algName, defClass=None):
    """ given a name, returns an alg object

    name can be name of a python module 
    or moduleName:className

    object or module needs to support the operation annotate(string) and the 
    variable "headers" or "writerTypes"

    defaultClass can be "Annotate" or "Map"
    """
    logging.debug("Creating algorithm object for %s " % (algName))
    if ":" in algName:
        filename, className = algName.split(":")
    else:
        filename, className = algName, None
    if filename.endswith(".pyc"):
        filename = filename.replace(".pyc", "")
    if not filename.endswith(".py"):
        filename = filename+".py"
    alg = loadPythonObject(filename, className, defClass=defClass)
    alg.algName = getAlgName(algName)
    return alg

def writeParamDict(paramDict, paramDictName):
    " pickle parameter to current dir "
    logging.debug("Writing parameters to %s" % paramDictName)
    for key, val in paramDict.iteritems():
        if val==None:
            logging.debug("parameter %s: None" % (key))
        elif type(val)==types.BooleanType:
            logging.debug("parameter %s: value %s" % (key, str(val)))
        elif type(val)!=types.IntType:
            logging.debug("parameter %s: %d values" % (key, len(val)))
        else:
            logging.debug("parameter %s: value %d" % (key, val))
    outFh = gzip.open(paramDictName, "wb")
    #cPickle.dump(paramDict, outFh)
    binData = marshal.dumps(paramDict)
    outFh.write(binData)
    outFh.close()
    return paramDictName

def findFiles(dataset):
    """ return all basenames for .gz files in datasets. 
    inDir can be a list of datasetnames, a file or a directory with datasetnames """

    #assert(type(datasets)==types.ListType)
    fnames = []
    dataDir = pubConf.resolveTextDir(dataset)
    if dataDir==None:
        raise Exception("error in input data spec")
    fnames.extend(glob.glob(join(dataDir, "*.articles.gz")))
    if len(fnames)==0:
        raise Exception("Could not find any *.articles.gz files in %s"% dataDir)

    return fnames

def findArticleBasenames(dataset, updateIds=None):
    """ given a fulltext directory, return all basenames of *.{article,files}.gz files 
        Basename means the part before the first "."
        Optionally filters on updateId
    
    """
    zipNames = findFiles(dataset)
    logging.debug("Found article files: %d files" % len(zipNames))
    baseNames = set([join(dirname(fn), basename(fn).split(".")[0]) for fn in zipNames])
    logging.debug("Found basenames: %d files" % len(baseNames))
    if updateIds!=None:
        filteredNames = []
        for updateId in updateIds:
            updateId = str(updateId)
            logging.log(5, "Keeping files that start with updateId %s" % updateId)
            filteredNames.extend([fn for fn in baseNames if basename(fn).startswith("%s_" % updateId)])
        baseNames = filteredNames
    logging.debug("Found %s basenames for %s: " % (len(baseNames), dataset))
    return baseNames

def findFilesSubmitJobs(algNames, algMethod, inDirs, outDirs, outExt, paramDict, runNow=False, cleanUp=False, updateIds=None, batchDir=".", runner=None, addFields=None):
    """ find data zip files and submit one map job per zip file
        Jobs call pubAlg.pyc and then run the algMethod-method of algName

        cleanUp: remove temporary files
        runNow: wil block until jobs are completed, then return

        If a list of updateIds is specified, run only on files with one of these updateIds
        Returns the list of baseNames, e.g. 0_00000,0_00001, etc that it ran on
    """
    assert(algMethod in ["map", "annotate"]) 

    if isinstance(inDirs, basestring):
        inDirs = [inDirs]
    if isinstance(algNames, basestring):
        algNames = algNames.split(",")
    if isinstance(outDirs, basestring):
        outDirs = outDirs.split(",")

    assert(len(algNames)==len(outDirs))

    paramDict["addFields"] = addFields
    paramDir = None

    # try to keep the parameter file somewhere where there is little 
    # risk of being overwritten by a concurrent batch
    if batchDir!=".":
        paramDir = batchDir

    if runner==None:
        logging.debug("Creating job runner")
        runner = maxRun.Runner(batchDir=batchDir)
    else:
        logging.debug("Batch runner was supplied")
        paramDir = runner.batchDir

    algCount = 0
    outNames = set()
    for algName, outDir in zip(algNames, outDirs):
        for inDir in inDirs:
            logging.debug("input directory %s" % inDir)
            baseNames = findArticleBasenames(inDir, updateIds)
            algShortName = basename(algName).split(".")[0]
            outDir = abspath(outDir)
            if paramDir==None:
                paramDir = outDir
            paramFname = join(paramDir, algShortName+".algParams.marshal.gz")
            # if multiple algs specified: try to make annotIds non-overlapping
            paramKey = "startAnnotId."+algShortName
            if paramKey not in paramDict and len(algNames)>1:
                paramDict[paramKey] = str(algCount*(10**pubConf.ANNOTDIGITS/len(algNames)))

            writeParamDict(paramDict, paramFname)
            for inFile in baseNames:
                inBase = splitext(basename(inFile))[0]
                inBase = basename(inDir)+"_"+inBase
                outNames.add(inBase)
                outFullname = join(outDir, inBase)+outExt
                #mustNotExist(outFullname) # should not hurt to avoid this check...
                if algName.startswith("java"):
                    executable = pubConf.jythonCmd
                    pyFname = __file__.replace(".pyc", ".py") # jython doesn't accept .pyc
                else:
                    executable = sys.executable # just the cpython binary
                    pyFname = __file__
                command = "%s %s %s %s %s {check out exists %s} %s" % \
                    (executable, pyFname, algName, algMethod, inFile, outFullname, paramFname)
                runner.submit(command)
            algCount += 1

    runner.finish(wait=runNow, cleanUp=cleanUp)
    if cleanUp:
        os.remove(paramFname)
    return list(outNames)
    
#def getDataIterator(alg, reader):
#    """ depending on the field "runOn" return the right
#     type of iterator of the reader 
#    """
#    if "runOn" in dir(alg):
#        if alg.runOn=="articles":
#            logging.debug("algorithm asked for only articles")
#            iterator = reader.iterArticles()
#        elif alg.runOn=="files":
#            logging.debug("algorithm asked for only files")
#            iterator = reader.iterFiles()
#        elif alg.runOn=="all" or alg.runOn=="both":
#            logging.debug("algorithm asked for files and articles")
#            iterator = reader.iterFileArticles()
#        else:
#            raise Exception("Illegal value for 'runOn' attribute in algorithm")
#    else:
#        logging.debug("algorithm did not specify any target data, selecting files & articles")
#        iterator = reader.iterFileArticles()
#    return iterator

pointRe = re.compile(r'[.] (?=[A-Z]|$)')

def findBestSnippet(text, start, end, minPos, maxPos, isLeft=False):
    " get end or start pos of best snippet for (start, end) in range (minPos, maxPos)"
    textLen = len(text)
        
    # make sure that (min,max) stays within string boundaries
    # and does not go into (start,end)
    if isLeft:
       minPos = max(0, minPos)
       maxPos = max(maxPos, 0)
       dotPos = text.rfind(". ", minPos, maxPos)
    else:
       minPos = max(0, minPos)
       maxPos = min(maxPos, textLen)
       #dotPos = text.find(". ", minPos, maxPos)
       # better: attempt to eliminate cases like E. coli 
       subText = text[minPos:minPos+250]
       match = None
       for m in pointRe.finditer(subText):
           match = m
           break
       if match!=None:
             dotPos = minPos+match.start()
       else:
             dotPos = -1

    if dotPos==-1:
        if isLeft:
            dotPos = maxPos
            if dotPos==start:
                dotPos=minPos
        else:
            dotPos = minPos
            if dotPos==end:
                dotPos=maxPos
    elif isLeft:
        dotPos+=2
    else:
        dotPos+=1

    return dotPos

def getSnippet(text, start, end, minContext=0, maxContext=150):
    """ return contextLen characters around start:end from text string 
    >>> textWithDot = 'cex XXX And'
    >>> Xpos = textWithDot.find("X")
    >>> getSnippet(textWithDot, Xpos, Xpos+3, minContext=5, maxContext=30)
    'cex <<<XXX>>> And'
    >>> textWithDot = 'XXX'
    >>> getSnippet(textWithDot, 0, 4, minContext=5, maxContext=30)
    '<<<XXX>>>'
    >>> textWithDot = 'A sentence without a dot yes XXX well there is no dot anywhere here'
    >>> Xpos = textWithDot.find("X")
    >>> getSnippet(textWithDot, Xpos, Xpos+3, minContext=5, maxContext=30)
    ' yes <<<XXX>>> well'
    >>> textWithDot = 'Hihi. bobo. X A sentence that starts with a dot.'
    >>> Xpos = textWithDot.find("X")
    >>> getSnippet(textWithDot, Xpos, Xpos+1, minContext=0, maxContext=50)
    '<<<X>>> A sentence that starts with a dot.'
    >>> textWithDot = 'A sentence. Another sentence. XXX. And yes a sentence. Oh my. Oh my.'
    >>> Xpos = textWithDot.find("X")
    >>> getSnippet(textWithDot, Xpos, Xpos+3, minContext=5, maxContext=30)
    'Another sentence. <<<XXX>>>. And yes a sentence.'
    >>> textWithDot = 'A sentence. Another sentence. XXX. E. coli is a great model organism, of course. '
    >>> getSnippet(textWithDot, Xpos, Xpos+3, minContext=5, maxContext=30)
    'Another sentence. <<<XXX>>>. E. coli is a great model organism, of course.'
    """
    start = int(start)
    end = int(end)
    rightDotPos = findBestSnippet(text, start, end, end+minContext, end+maxContext, isLeft=False)
    leftDotPos = findBestSnippet(text, start, end, start-maxContext, start-minContext, isLeft=True)

    leftSnip = text[leftDotPos:start]
    mainSnip = text[start:end]
    rightSnip = text[end:rightDotPos]
    snippet = leftSnip+"<<<"+mainSnip+">>>"+rightSnip
    snippet = snippet.replace("\n", " ")
    snippet = snippet.replace("\t", " ")
    return snippet

#def writeAnnotations(alg, articleData, fileData, outFh, annotIdAdd, doSectioning, addFields):
def iterAnnotRows(alg, articleData, fileData, annotIdAdd, doSectioning, addFields):
    """ use alg to annotate fileData, yield rows, adding annotIdAdd to all annotations 
    return next free annotation id.
    """
    annotDigits = int(pubConf.ANNOTDIGITS)
    fileDigits = int(pubConf.FILEDIGITS)
    annotIdStart = (int(fileData.fileId) * (10**annotDigits)) + annotIdAdd
    logging.debug("extId %s, fileId %s, annotIdStart %d, fileLen %d" \
        % (articleData.externalId, fileData.fileId, annotIdStart, len(fileData.content)))

    text = fileData.content.replace("\a", "\n")

    if fileData.fileType=="supp":
        sections = {"supplement": (0, len(text))}
    else:
        allTextSections = {"unknown": (0, len(text))}
        if doSectioning:
            sections = pubGeneric.sectionRanges(text)
            if sections==None:
                sections = allTextSections
        else:
            sections = allTextSections

    annotCount = 0
    for section, sectionRange in sections.iteritems():
        secStart, secEnd = sectionRange
        if section!="unknown":
            logging.debug("Annotating section %s, from %d to %d" % (section, secStart, secEnd))
        secText = text[secStart:secEnd]
        fileData = fileData._replace(content=secText)
        annots = alg.annotateFile(articleData, fileData)
        if annots==None:
            logging.debug("No annotations received")
            continue

        for row in annots:
            # prefix with fileId, extId
            logging.debug("received annotation row: %s" %  str(row))
            fields = ["%018d" % (int(annotIdStart)+annotCount)]
            if articleData!=None:
                extId = articleData.externalId
            else:
                extId = "0"
            fields.append(extId)
            # add addFields
            artDict = articleData._asdict()
            if addFields!=None:
                for addField in addFields:
                    fields.append(artDict.get(addField, ""))
            # add other fields
            try:
                fields.extend(row)
            except TypeError:
                raise Exception("return type from annotator is not iterable. It needs to be a list, set or similar")

            # check if alg actually returns coordinates
            if alg.headers[0]=="start" and alg.headers[1]=="end":
                start, end = row[0:2]
                if (start,end) == (0,0):
                    snippet = None
                else:
                    snippet = getSnippet(secText, start, end)
                    # lift start and end if sectioning
                    start = secStart+int(start)
                    end = secStart+int(end)

                # postfix with snippet
                logging.debug("Got row: %s" % str(row))
                if doSectioning:
                    fields.append(section)
                if snippet!=None:
                    fields.append(snippet)
            #fields = [unicode(x).encode("utf8") for x in fields]
            fields = [pubStore.removeTabNl(unicode(x)) for x in fields]
                
            #line = "\t".join(fields)
            #outFh.write(line+"\n")
            annotCount+=1
            assert(annotCount<10**annotDigits) # we can only store 100.000 annotations per file
            yield fields

def getHeaders(alg, doSectioning, addFields):
    if "headers" not in dir(alg) and not "headers" in alg.__dict__:
        logging.error("headers variable not found.")
        logging.error("You need to define a variable 'headers' in your python file or class")
        sys.exit(1)

    assert(type(alg.headers)==types.ListType)

    headers = copy.copy(alg.headers)
    headers.insert(0, "annotId")
    headers.insert(1, "externalId")
    if addFields!=None:
        for i, addField in enumerate(addFields):
            headers.insert(2+i, addField)

    if doSectioning:
        headers.append("section")

    if not "snippet" in headers and "start" in headers and "end" in headers:
        headers.append("snippet")
    return headers

def writeHeaders(alg, outFh, doSectioning, addFields):
    """ write headers from algorithm to outFh, 
    add a section field if doSectioning is true
    add fields from addFields list after the external id
    """
    headers = getHeaders(alg, doSectioning, addFields)
    logging.debug("Writing headers %s to %s" % (headers, outFh.name))
    outFh.write("\t".join(headers)+"\n")

def getAlgName(algName):
    " return name of algorithm: either name of module or name of class "
    algName = algName.split(":")[0]
    algName = algName.split(".")[0]
    algName = basename(algName)
    #logging.debug("alg is %s" % dir(alg))
    #logging.debug("alg is %s" % dir(alg.__name__))
    #algName = alg.__class__.__name__
    #if algName=="module":
        #algName = alg.__name__
    logging.debug("Algorithm name is %s" % algName)
    return algName

def getAnnotId(alg, paramDict):
    """ return annotId configured by paramDict with parameter startAnnotId.<algName>, 
    remove parameter from paramDict
    """
    algName = alg.algName
    paramName = "startAnnotId."+algName
    logging.debug("Start annotId can be defined with parameter %s" % paramName)

    annotIdAdd = int(paramDict.get(paramName, 0))
    if paramDict.get(paramName, None):
        del paramDict[paramName]
    logging.debug("Start annotId is %d" % annotIdAdd)
    return annotIdAdd

def makeLocalTempFile():
    " create tmp file on local harddisk "
    fd, tmpOutFname = tempfile.mkstemp(dir=pubConf.getTempDir(), prefix="pubRun", suffix=".tab")
    os.close(fd)
    logging.debug("local temporary file is %s" % tmpOutFname)
    return tmpOutFname

def moveTempToFinal(tmpOutFname, outFname):
    " copy from temp to final out destination fname "
    logging.debug("Copying %s to %s" % (tmpOutFname, outFname))
    outDir = dirname(outFname)
    if outDir!="" and not isdir(outDir):
        os.makedirs(outDir)
    shutil.copy(tmpOutFname, outFname)
    os.remove(tmpOutFname)

def attributeTrue(obj, attrName):
    " returns true if obj has attribute and it is true "
    if attrName in dir(obj):
        if obj.__dict__[attrName]==True:
            return True
    return False

def openOutfiles(outName, outTypes):
    """ open one temporary file per outType. return dict type -> filehandle and
        dict type -> final filename 
    """
    chunkId = basename(outName).split(".")[0] # e.g. pmc_0_00000
    finalBase = join(dirname(outName), chunkId)
    tmpBase = join(pubConf.TEMPDIR, chunkId)
    tmpOutFiles = {}
    finalOutFnames = {}
    for ext in outTypes:
        tmpOutFiles[ext] = open(tmpBase+"."+ext, "w")
        finalOutFnames[ext] = finalBase+"."+ext
    return tmpOutFiles, finalOutFnames

def moveResults(outFiles, finalOutNames):
    " move from scratch/tmp to server "
    for ext, outFile in outFiles.iteritems():
        outFile.close()
        logging.info("Moving %s to %s" % (outFile.name, finalOutNames[ext]))
        shutil.move(outFile.name, finalOutNames[ext])

def runAnnotateWrite(reader, alg, paramDict, outName):
    """ run annotate of alg on all articles in reader """
    if "setup" in dir(alg):
        logging.debug("Running setup")
        alg.setup(paramDict)

    outFiles, finalNames = openOutfiles(outName, alg.outTypes)
    if "startup" in dir(alg):
        logging.debug("Running startup")
        alg.startup(outFiles)

    onlyMain, onlyMeta, bestMain = getAlgPrefs(alg, paramDict)
    for articleData, fileDataList in reader.iterArticlesFileList(onlyMeta, bestMain, onlyMain):
        alg.annotate(articleData, fileDataList)

    if "cleanup" in dir(alg):
        logging.debug("Running cleanup")
        alg.cleanup()

    moveResults(outFiles, finalNames)

def getAlgPrefs(alg, paramDict):
    onlyMain = attributeTrue(alg, "onlyMain")
    onlyMain = paramDict.get("onlyMain", onlyMain)
    if isinstance(onlyMain, basestring):
        onlyMain = (onlyMain.lower()=="true")
    logging.info("Only main files: %s" % onlyMain)

    onlyMeta = attributeTrue(alg, "onlyMeta")
    logging.info("Only meta files: %s" % onlyMeta)

    bestMain = attributeTrue(alg, "bestMain")
    logging.info("Only best main files: %s" % bestMain)
    return onlyMain, onlyMeta, bestMain


def runAnnotate(reader, alg, paramDict, outName):
    """ annotate all articles in reader, write to outName in an atomic way via tempfile
    """
    tmpOutFname = makeLocalTempFile()

    if outName=="stdout":
        outFh = sys.stdout
    else:
        outFh = pubStore.utf8GzWriter(tmpOutFname)

    doSectioning = attributeTrue(alg, "sectioning")
    logging.debug("Sectioning activated: %s" % doSectioning)
    addFields = paramDict.get("addFields", [])

    writeHeaders(alg, outFh, doSectioning, addFields)

    for row in runAnnotateIter(reader, alg, paramDict, doSectioning, addFields):
        line = "\t".join(row)
        outFh.write(line)
        outFh.write("\n")

    if outName!="stdout":
        outFh.close()
        moveTempToFinal(tmpOutFname, outName)
        
def runAnnotateIter(reader, alg, paramDict, doSectioning=None, addFields=None):
    """ annotate all articles in reader and yield a list of fields
    """
    if "startup" in dir(alg):
        logging.debug("Running startup")
        alg.startup(paramDict)

    annotIdAdd = getAnnotId(alg, paramDict)
    onlyMain, onlyMeta, bestMain = getAlgPrefs(alg, paramDict)

    for articleData, fileDataList in reader.iterArticlesFileList(onlyMeta, bestMain, onlyMain):
        logging.debug("Annotating article %s with %d files, %s" % \
            (articleData.articleId, len(fileDataList), [x.fileId for x in fileDataList]))
        for fileData in fileDataList:
            for row in iterAnnotRows(alg, articleData, fileData, annotIdAdd, doSectioning, addFields):
                yield row

def unmarshal(fname):
    if fname.endswith(".gz"):
        with gzip.open(fname, "rb") as f:
            raw = f.read()
            data = marshal.loads(raw)
    else:
        with open(fname, "rb") as f:
            data = marshal.load(f)
    return data

def runCombine(inFname, alg, paramDict, outName):
    inFnames = open(inFname).read().splitlines()
    data = {}
    if "combineStartup" in dir(alg):
        alg.combineStartup(data, paramDict)

    for fname in inFnames:
        partDict = unmarshal(fname)
        alg.combine(data, partDict, paramDict)

    if "combineCleanup" in dir(alg):
        data = alg.combineCleanup(data)

    f = open(outName, "wb")
    marshal.dump(data, f)
    f.close()

def runMap(reader, alg, paramDict, outFname):
    """ run map part of alg over all files that reader has.
        serialize results ('pickle') to outFname 
        
        input can be a reader or a directory
        alg can be a string or an alg object 
    """
    logging.info("Running map step")
    tmpOutFname = makeLocalTempFile()

    results = {}
    if "startup" in dir(alg):
        alg.startup(paramDict, results)

    # run data through algorithm
    onlyMeta = attributeTrue(alg, "onlyMeta")
    bestMain = attributeTrue(alg, "bestMain")

    for articleData, fileDataList in reader.iterArticlesFileList(onlyMeta, bestMain):
        logging.debug("Running on article id %s" % articleData.articleId)
        for fileData in fileDataList:
            logging.debug("Running on file id %s" % fileData.fileId)
            text = fileData.content
            alg.map(articleData, fileData, text, results)

    if "end" in dir(alg):
        results = alg.end(results)

    outFh = gzip.open(tmpOutFname, "wb")
    binData = marshal.dumps(results)
    outFh.write(binData)
    outFh.close()
    del binData

    moveTempToFinal(tmpOutFname, outFname)

def runReduce(algName, paramDict, path, outFilename, quiet=False, inFnames=None):
    """ parse pickled dicts from path, run through reduce function of alg and 
    write output to one file """

    if outFilename!=None and isfile(outFilename):
        logging.info("deleting existing file %s" % outFilename)
        os.remove(outFilename)

    if isinstance(algName, basestring):
        alg = getAlg(algName, defClass="Map")
    else:
        alg = algName

    if "map" not in dir(alg):
        logging.error("There is not map() function in %s" % algName)
        sys.exit(1)

    if "startup" in dir(alg):
        alg.startup(paramDict, {})

    if inFnames!=None:
        infiles = inFnames
    elif isfile(path):
        logging.debug("Filename specified, running only on a single file (debugging)")
        infiles = [(dirname(path), path)]
    else:
        infiles = pubGeneric.findFiles(path, [MAPREDUCEEXT])
    
    if len(infiles)==0:
        logging.error("Could not find any %s files in %s" % (MAPREDUCEEXT, path))
        sys.exit(1)

    # read pickle files into data dict
    data = {}
    fileCount = 0
    logging.info("Reading map output")
    meter = maxCommon.ProgressMeter(len(infiles), quiet=quiet, stepCount=100)
    for relDir, fileName in infiles:
        binData = gzip.open(fileName, "rb").read()
        nodeData = marshal.loads(binData)
        del binData
        for key, values in nodeData.iteritems():
            if not hasattr(values, "__iter__"):
                values = [values]
            # major change: append instead of extend
            # will break existing mr-scripts
            data.setdefault(key, []).append(values)
        fileCount += 1
        logging.debug("Reading "+fileName)
        meter.taskCompleted()

    logging.info("Writing to %s" % outFilename)
    if outFilename==None:
        ofh = None
    elif outFilename=="stdout":
        ofh = sys.stdout
    else:
        ofh = open(outFilename, "w")

    if "headers" in dir(alg) and ofh!=None:
        ofh.write("\t".join(alg.headers))
        ofh.write("\n")

    if "reduceStartup" in dir(alg):
        logging.info("Running reduceStartup")
        alg.reduceStartup(data, paramDict, ofh)

    logging.info("Running data through reducer")
    meter = maxCommon.ProgressMeter(len(data))
    for key, valList in data.iteritems():
        tupleIterator = alg.reduce(key, valList)
        for tuple in tupleIterator:
            if tuple==None:
                logging.debug("Got None, not writing anything")
                continue
            if type(tuple)==types.StringType: # make sure that returned value is a list
                tuple = [tuple]
            if type(tuple)==types.IntType: # make sure that it's a string
                tuple = [str(tuple)]
            tuple = [unicode(x).encode("utf8") for x in tuple] # convert to utf8
            if ofh!=None:
                ofh.write("\t".join(tuple))
                ofh.write("\n")
        meter.taskCompleted()
    if ofh!=None:
        ofh.close()

    if "reduceEnd" in dir(alg):
        logging.info("Running reduceEnd")
        alg.reduceEnd(data)

def concatFiles(inDir, outFname):
    " concat all files in outDir and write to outFname. "
    logging.info("Looking for tab.gz files in %s" % inDir)
    inFnames = pubGeneric.findFiles(inDir, ".tab.gz")
    ofh = open(outFname, "w")
    pm = maxCommon.ProgressMeter(len(inFnames))
    logging.info("Concatting...")
    fno = 0
    for relDir, fn in inFnames:
        lno = 0
        for line in gzip.open(fn):
            if lno==0 and fno==0:
                ofh.write(line)
            if lno!=0:
                ofh.write(line)
            lno += 1
        pm.taskCompleted()
        fno += 1
    ofh.close()

def getLastOutType(alg, paramDict):
    if "setup" in dir(alg):
        logging.debug("Running setup")
        alg.setup(paramDict)
    assert(type(alg.outTypes)==types.ListType)
    assert(len(set(alg.outTypes))==len(alg.outTypes)) # no duplicate out type
    outExt = alg.outTypes[-1]
    return outExt

def splitList(a, n):
    k, m = len(a) / n, len(a) % n
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in xrange(n))

def writeParts(ll, outDir):
    " writes lines to numbered textFiles in outDir "
    fnames = []
    for i, lines in enumerate(ll):
        fname = join(outDir, "inputFiles%d.txt" % i)
        ofh = open(fname)
        ofh.write("\n".join(lines))
        ofh.write("\n")
        ofh.close()
        fnames.append(fname)
    return fnames

def submitCombine(runner, algName, mapReduceDir, outExt, paramDict, pieceCount):
    " submits combiner jobs: they get a list of dicts and output a single dict "
    inFnames = pubGeneric.findFiles(mapReduceDir, [MAPREDUCEEXT])
    random.shuffle(inFnames)
    parts = splitList(inFnames, pieceCount)
    partFnames = writeParts(parts, runner.batchDir)

    paramFname = join(runner.batchDir, "mapReduceParams.marshal.gz")
    writeParamDict(paramDict, paramFname)
    for fname in partFnames:
        inBase   = splitext(basename(fname))[0]
        outFullname = join(mapReduceDir, inBase+".combined."+MAPREDUCEEXT.replace(".gz",""))
        command = "%s %s %s %s %s {check out exists %s} %s" % \
                (sys.executable, __file__ , algName, "combine", fname, outFullname, paramFname)
        runner.submit(command)
    runner.finish()

def submitAnnotateWrite(runner, algName, textDirs, paramDict, outDir, updateIds=None):
    """ 
    submit annotation writer jobs to batch system 

    The only difference from anntation jobs are that annotation writers need to declare what
    types of data they return in the list "outTypes". Their startup method gets a dictionary
    with file object, one per outType. The annotators must then write their output themselves
    into the files. The annotate function does not return anything.

    """
    alg = pubAlg.getAlg(algName)
    outExt = getLastOutType(alg, paramDict)

    outNames = []
    paramFname = join(runner.batchDir, "algParams.marshal.gz")
    writeParamDict(paramDict, paramFname)

    for textDir in textDirs:
        logging.debug("input directory %s" % textDir)
        baseNames = findArticleBasenames(textDir, updateIds)
        for inFname in baseNames:
            # outName: e.g pmc_0_0000 for sth like 0_00000.articles.gz 
            outName = basename(textDir)+"_"+splitext(basename(inFname))[0]
            outNames.append(outName)
            # outFullName: e.g <path>/pmc_0_0000.svml 
            outFullname = join(outDir, outName)+"."+outExt
            command = "%s %s %s %s %s {check out exists %s} %s" % \
                (sys.executable, __file__ , algName, "annotateWrite", inFname, outFullname, paramFname)
            runner.submit(command)
    return outNames

def testAlg(algName, paramDict):
    logging.debug("Testing algorithm %s startup" % algName)
    alg = getAlg(algName, defClass="Annotate") # just to check if algName is valid

    if "annotateFile" not in dir(alg) and "annotateWrite" not in dir(alg):
        logging.error("Could not find an annotateFile() function in %s" % algName)
        sys.exit(1)

    if "startup" in dir(alg):
        alg.startup(paramDict) # to check if at least the algorithm works 

def annotate(algNames, textDirs, paramDict, outDirs, cleanUp=False, runNow=False, \
    updateIds=None, batchDir=".", runner=None, addFields=[], concat=False):
    """ 
    submit jobs to batch system to run algorithm over text in textDir, write
    annotations to outDir 

    algNames can be a comma-sep list of names
    outDirs can be a comma-sep list of directories
    cleanUp deletes all cluster system tempfiles
    runNow waits until jobs have finished
    concat will concatenate all output files and write to outDir (actually a textfile)
    """
    if isinstance(algNames, basestring):
        algNames = algNames.split(",")
    if isinstance(outDirs, basestring):
        outDirs = outDirs.split(",")

    for algName in algNames:
        if not algName.startswith("java"):
            testAlg(algName, paramDict)

    logging.debug("Testing successful, submitting jobs")
    baseNames = findFilesSubmitJobs(algNames, "annotate", textDirs, outDirs, \
        ".tab.gz", paramDict, runNow=runNow, cleanUp=cleanUp, updateIds=updateIds, \
        batchDir=batchDir, runner=runner, addFields=addFields)
    
    if concat:
        for outDir in outDirs:
            outFname = outDir+".tab"
            concatFiles(outDir, outFname)
            logging.info("Output written to %s" % outFname)
    return baseNames

def mapReduceTestRun(datasets, alg, paramDict, tmpDir, updateIds=None, skipMap=False, keepOutFile=False):
    " do a map reduce run only on one random file, no cluster submission, for testing "
    if updateIds!=None and len(updateIds)!=0:
        updateId = updateIds[0]
    else:
        updateId = None
    baseNames = findArticleBasenames(datasets[0], updateId)
    firstBasename = baseNames.pop()
    oneInputFile = firstBasename+".articles.gz"
    if not isfile(oneInputFile):
        oneInputFile = firstBasename+".files.gz"
    logging.info("Testing algorithm on file %s" % oneInputFile)
    reader = pubStore.PubReaderFile(oneInputFile)
    tmpAlgOut = join(tmpDir, "pubMapReduceTest.temp.marshal.gz")
    tmpRedOut = join(tmpDir, "red.temp.tab")
    if not skipMap:
        runMap(reader, alg, paramDict, tmpAlgOut)
    if "combine" in dir(alg):
        runCombine(tmpAlgOut, alg, paramDict, tmpAlgOut)
    runReduce(alg, paramDict, tmpAlgOut, tmpRedOut, quiet=True)

    ifh = open(tmpRedOut)
    logging.info("Example reducer output")
    for i in range(0, 50):
        line = ifh.readline()
        line = line.strip()
        logging.info(line)
    os.remove(tmpAlgOut)
    if keepOutFile:
        logging.info("test output written to file %s, file not deleted" % tmpRedOut)
    else:
        logging.info("Waiting for 5 secs")
        time.sleep(5)
        os.remove(tmpRedOut)

def mapReduce(algName, textDirs, paramDict, outFilename, skipMap=False, cleanUp=False, \
        tmpDir=None, updateIds=None, runTest=True, batchDir=".", headNode=None, \
        runner=None, onlyTest=False, combineCount=50):
    """ 
    submit jobs to batch system to:
    create tempDir, map textDir into this directory with alg,
    then reduce from tmpDir to outFilename 

    will test the algorithm on a random input file first
    if updateIds is set, will only run on files like <updateId>_*, otherwise on all files
    """

    logging.debug("Running map/reduce on text directories %s" % textDirs)
    alg = getAlg(algName, defClass="Map") # just to check if algName is valid

    if isinstance(textDirs, basestring):
        textDirs = [textDirs]

    if tmpDir==None:
        # if possible, place this into the batchDir, so two concurrent batches don't clash
        if runner!=None:
            tmpDir = join(runner.batchDir, "mapReduceTmp")
        else:
            tmpDir = join(pubConf.mapReduceTmpDir, os.path.basename(algName).split(".")[0])

    if skipMap:
        assert(isdir(tmpDir))
    else:
        if isdir(tmpDir):
            logging.info("Deleting map/reduce temp directory %s" % tmpDir)
            shutil.rmtree(tmpDir)
        logging.info("Creating directory %s" % tmpDir)
        os.makedirs(tmpDir)

    if "batchStartup" in dir(alg):
        logging.info("Running batchStartup")
        alg.batchStartup(paramDict)

    # before we let this loose on the cluster, make sure that it actually works
    if runTest and not skipMap:
        mapReduceTestRun(textDirs, alg, paramDict, tmpDir, updateIds=updateIds, \
            skipMap=skipMap, keepOutFile=onlyTest)
        # make sure that all state of the algorithm is reset
        del alg
        alg = getAlg(algName, defClass="Map") # just to check if algName is valid

    if not onlyTest:
        if not skipMap:
            logging.info("Now submitting to cluster/running on all files")
            findFilesSubmitJobs(algName, "map", textDirs, tmpDir, MAPREDUCEEXT, paramDict,\
                runNow=True, cleanUp=cleanUp, updateIds=updateIds, batchDir=batchDir, runner=runner)

        combFnames = None
        if "combine" in dir(alg):
            outExt = ".combined"+MAPREDUCEEXT.replace(".gz", "")
            submitCombine(runner, algName, tmpDir, outExt, paramDict, combineCount)
            combFnames = glob.glob(join(tmpDir, "*"+outExt))
        runReduce(algName, paramDict, tmpDir, outFilename, inFnames=combFnames)

    if "cleanup" in dir(alg):
        logging.info("Running cleanup")
        alg.cleanup()
        
    if cleanUp and not skipMap:
        logging.info("Deleting directory %s" % tmpDir)
        shutil.rmtree(tmpDir)

if __name__ == '__main__':
    parser = optparse.OptionParser("""this module is calling itself. 
    syntax: pubAlg.py <algName> map|reduce <inFile> <outFile> <paramPickleFile>
    """)
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="show debug messages")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="show more debug messages")
    (options, args) = parser.parse_args()
    pubGeneric.setupLogging(__file__, options)

    if len(args)==0:
        doctest.testmod()
        sys.exit(0)

    algName, algMethod, inName, outName, paramFile = args

    binData = gzip.open(paramFile, "rb").read()
    paramDict = marshal.loads(binData)
    for key, val in paramDict.iteritems():
        logging.log(5, "parameter %s = %s" % (key, str(val)))

    alg = pubAlg.getAlg(algName, defClass=string.capitalize(algMethod))

    if algMethod!="combine":
        reader = pubStore.PubReaderFile(inName)
        if algMethod=="map":
            runMap(reader, alg, paramDict, outName)
        elif algMethod=="annotate":
            runAnnotate(reader, alg, paramDict, outName)
        elif algMethod=="annotateWrite":
            runAnnotateWrite(reader, alg, paramDict, outName)
    else:
        runCombine(inName, alg, paramDict, outName)

    reader.close()
    
