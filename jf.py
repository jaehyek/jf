#!/usr/bin/python3

'''
Created on 2011. 7. 31.

@author: jaehyek
'''
from  __future__ import print_function

import os , argparse, time, sys
# from Crypto.Util.RFC1751 import wordlist
import re, glob



# variables.
dirskiplist = []
findlog = ''
findtext = ''
finddir = []
findfile = ''
commandOnFile = ''
findconfig = ''
findtre = False
findfre = False
boolfnmatch = False

refindtext = 0
refindfile = 0

countFilenameMatched = 0
countTextMatched = 0

fileskiptype = ['.a', '.o', '.so', '.mp3', '.ko', '.zip', '.tar', '.bz', '.apk',
                '.png', '.jpg', '.jar', '.dex', '.rle', '.cmd', '.pyd', '.pyc', '.exe']

class Tee(object):
    def __init__(self, name):
        self.file = open(name, "a")
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

def findtextinfile(filename):
    global dirskiplist, findlog, findtext, finddir, findfile, commandOnFile
    global findconfig, findtre, findfre, boolfnmatch
    global refindtext, refindfile, countFilenameMatched, countTextMatched

    nbytes = os.path.getsize(filename)
    nbytes = nbytes >> 20
    if( nbytes > 5 ) :
        print (' too big file over 5MB : ' + filename)
        return

    linenumber = 0
    found = 0
    try:
        for textline in open ( filename, 'r'):
            linenumber += 1
            listfindstr = []
            if findtre == True :
                listfindstr = refindtext.findall(textline, re.IGNORECASE)
            else:
                listfindstr.append( findtext )

            for findstr in listfindstr :
                pos = textline.lower().find(findstr.lower(), 0)
                if (pos != -1 ):
                    found = 1
                    # check and skip the long sentense
                    linelength = len(textline)
                    if linelength > 100 :
                        endpos = pos + len(findstr) + 10
                        if endpos > (linelength-1):
                            endpos = linelength -1
                        startpos = pos - 10
                        if ( startpos < 0 ):
                            startpos = 0
                        textline = textline[startpos:endpos]
                    textline = textline.strip()
                    msg =  os.path.abspath(filename) + '.' + str(linenumber) + "::  " + textline
                    print (msg)
                else:
                    found = 0
            if found == 1 :
                countTextMatched += 1
    except:
        print("*** Except raised inside of %s. *** "%filename)


def isdirskip(strpath):
    if len( dirskiplist ) == 0 :
        return False
    tmpstrpath = os.path.abspath(strpath)
    for dirskip  in dirskiplist :
        if dirskip  in tmpstrpath :
            return True
    return False



def isAllowedFileType( strfile ):
    # check the extension of file.
    basename, extension = os.path.splitext(strfile)
    if   extension in fileskiptype:
            return False
    else:
        return True

deletechars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, deletechars))
def isBinaryFile( filename ):
    return is_binary_string(open(filename, 'rb').read(1024))

def runCommand( filename, commandOnFile ):
    tmpCommand = commandOnFile
    if tmpCommand.find("%(a)s") >= 0 :
        dicta = { 'a': filename }
        tmpCommand = tmpCommand % dicta
    elif  tmpCommand.find("%s") >= 0 :
        tmpCommand = tmpCommand % ( filename )
    print ("Executing :  " , tmpCommand)
    os.system(tmpCommand)

import fnmatch
'''
PatternMeaningforfnmatch
* : matches everything
? : any single character
[seq] : matches any character in seq
[!seq] : matches any character not in seq
'''

def findAtDir ( strpath ):     # always strpath is a start point to search .
    global dirskiplist, findlog, findtext, finddir, findfile, commandOnFile
    global findconfig, findtre, findfre, boolfnmatch
    global refindtext, refindfile, countFilenameMatched, countTextMatched

    for root, dirs, files in os.walk(strpath):
        # first, check the skip dir "
        if isdirskip(root) :
            continue

        if boolfnmatch == True :
            files=[aa for aa in files if fnmatch.fnmatch(aa.lower(), findfile)],
        elif findfre == True :
            files = [aa for aa in files if len(refindfile.findall(aa)) > 0 ]
        elif len(findfile)> 0 :
            files = [ aa for aa in files if findfile in aa.lower() ]

        # count if matching
        if len(findfile) > 0 :
            countFilenameMatched += len(files)

        for filename in files:
            # second, check if the wanted file for each filename
            absfilename = os.path.abspath(os.path.join( root,  filename))
            if os.path.islink(absfilename):
                continue

            if len(findtext) == 0:
                # just find a file
                strtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(absfilename)) )
                strsize = os.path.getsize(absfilename)
                msg = filename + ' : ' + strtime + ': ' + str(strsize) + ' bytes'
                print (msg)
                if len(commandOnFile) > 0 :
                    runCommand( absfilename, commandOnFile )
            else:
                if (isAllowedFileType( absfilename) == True) and ( isBinaryFile(absfilename) == False) :
                    findtextinfile( absfilename)




if __name__ == "__main__":

    tooldescription = '''
    Search a text recursively within directory.
    in case of file searching,  *.? [ , ] are availavle to use .
    * : matches everything
    ? : any single character
    [seq] : matches any character in seq
    [!seq] : matches any character not in seq
    '''

    cmdlineopt = argparse.ArgumentParser(description=tooldescription)
    cmdlineopt.add_argument('-t', action="store", dest="findtext", default='',  help='text pattern to find' )
    cmdlineopt.add_argument('-dirskip', action='append', dest='dirskiplist', default=[], help='Add a subpath to be skip to a dirskiplist',)
    cmdlineopt.add_argument('-l', action="store", dest="findlog", default='',  help='set log file for output' )
    cmdlineopt.add_argument('-d', action="append", dest="finddir", default=[], help='Add a path to find to the path',)
    cmdlineopt.add_argument('-f', action="store", dest="findfile", default='',  help='file pattern to find' )
    cmdlineopt.add_argument('-fexe', action="store", dest="commandOnFile", default='', help='execute a command , sample : dir percent(s), or dir percent(a)s' )
    cmdlineopt.add_argument('-config', action="store", dest="findconfig", default='', help='assign the path to find' )
    cmdlineopt.add_argument('-default', action="store_true", dest="finddefault",  default=False, help='default path to config file. default = ~/.jf.txt' )
    cmdlineopt.add_argument('-tre', action="store_true", dest="findtre",  default=False, help='Using regular exepression, search, sort and print a word containg the findtext of -t opition' )
    cmdlineopt.add_argument('-fre', action="store_true", dest="findfre",  default=False, help='file matching pattern using regular express ' )

    cmdlineresults = cmdlineopt.parse_args()

    if( cmdlineresults.finddefault ):
        findconfig = r'~/.jf.txt'
    elif(len(cmdlineresults.findconfig) > 0  ):
        findconfig = cmdlineresults.findconfig

    if(len(findconfig) > 0   ):
        findconfig = os.path.expanduser (findconfig)

    if(len(findconfig) > 0  ) and ( os.path.isfile(findconfig)):
        filecommandtmp = []
        with open( findconfig, 'r') as fconfig:
            for line in fconfig:
                if line[0] == '#' :
                    continue
                filecommandtmp += [line]
        filecommandstr = ' '.join(filecommandtmp)
        print (filecommandstr.split(None))

        fileparser = argparse.ArgumentParser()
        fileparser.add_argument('-t', action="store", dest="findtext", default='')
        fileparser.add_argument('-dirskip', action='append', dest='dirskiplist', default=[], help='Add a subpath to be skip to a dirskiplist',)
        fileparser.add_argument('-l', action="store", dest="findlog", default='', help=' create the log file during finding')
        fileparser.add_argument('-d', action="append", dest="finddir", default=[], help='Add a path to find to the path',)
        fileparser.add_argument('-f', action="store", dest="findfile", default='', help='file to find')
        fileparser.add_argument('-fexe', action="store", dest="commandOnFile", default='' , help=' find files with same file length')
        fileparser.add_argument('-config', action="store", dest="findconfig", default='', help='indicate the config file to find' )
        fileparser.add_argument('-default', action="store_true", dest="finddefault",  default=False, help='use the default config file')
        fileparser.add_argument('-tre', action="store_true", dest="findtre",  default=False, help='Using regular exepression, search, sort and print a word containg the findtext of -t opition' )
        fileparser.add_argument('-fre', action="store_true", dest="findfre",  default=False, help='file matching pattern using regular express ' )

        fileresults = fileparser.parse_args( filecommandstr.split(None) )

        cmdlineresults = fileresults

    findlog = cmdlineresults.findlog
    finddir = cmdlineresults.finddir
    findfile = cmdlineresults.findfile
    commandOnFile = cmdlineresults.commandOnFile
    dirskiplist = cmdlineresults.dirskiplist
    findtext = cmdlineresults.findtext
    findtre = cmdlineresults.findtre
    findfre = cmdlineresults.findfre


    if len(finddir) == 0  :
        finddir = [ os.getcwd() ]

    if len(findlog) > 0 :
        findlog = os.path.expanduser(findlog)

    findfile = findfile.lower()
    findtext = findtext.lower()

    for i in range( len(finddir) ):
        finddir[i] = os.path.expanduser(finddir[i])
        finddir[i] = os.path.abspath(finddir[i])
        if os.path.isdir(finddir[i]) == False :
            print ("path doesn't exit")
            exit()

    # convert the dirskiplist to abs path
    if len(dirskiplist) > 0 :
        for i in range(len(dirskiplist)) :
            dirskiplist[i] = os.path.expanduser(dirskiplist[i])
            dirskiplist[i] = os.path.abspath(dirskiplist[i])

    print ('findtext =', findtext)
    print ('findconfig =', findconfig)
    print ('findlog =', findlog)
    print ('finddir =', finddir)
    print ('findfile = ', findfile)
    print ('commandOnFile = ', commandOnFile)
    print ('dirskiplist =', dirskiplist)
    print ('findtre =', findtre)
    print ('findfre =', findfre)
    print ("~~~~~~~~~~~~~~~~~~~~~~~ ver 2015.10.26 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


    if len(findtext) == 0 and len(findfile) == 0 :
        print ("No text or no file to find ... ")
        exit()

    if len(findlog) > 0 :
        ObjectTee = Tee(findlog)

    if(findtre and len(findtext) >0 ):
        refindtext = re.compile( findtext, re.IGNORECASE)

    if(findfre and len(findfile) >0 ):
        refindfile = re.compile( findfile, re.IGNORECASE)
    else:
        listfnchar = ['*', '?', '[', ']', '!']
        if [1 for aa in listfnchar if aa in findfile ].count(1) > 0 :
            boolfnmatch = True

    dirsave = os.getcwd()
    for tmppath in finddir :
        if os.path.islink(tmppath):
            continue
        os.chdir(tmppath)
        findAtDir ( tmppath )
        os.chdir(dirsave)
        print ('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        if len(findfile) > 0 :
            print (" the filename-matched file count : ", countFilenameMatched)
        if len(findtext) > 0 :
            print (" the text-searched file count : ", countTextMatched)


    if len(findlog) > 0 :
        del ObjectTee




