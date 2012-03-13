#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
import string
import argparse

def parseOptions():
    argParser = argparse.ArgumentParser(
        description='inserts constants for attributes and parameters in Method files. (requires python >= 2.7)'
    )
    argParser.add_argument('familiesFolder',
        help = 'families folder',
        nargs = '?',
        default = os.path.relpath(os.path.join(os.path.dirname(__file__), '..', 'Families')))
    argParser.add_argument('--familyFile',
        help = 'csv file (use it several times)',
        action = 'append',
        dest = 'csvFiles'),
    argParser.add_argument('-v', '--verbose',
        help = 'verbose',
        action = 'count',
        dest = 'verbosity')
    args = argParser.parse_args()
    if(not args.csvFiles):
        args.csvFiles = getFamilyFiles(args.familiesFolder)
    return args

def getFamilyFiles(familiesFolder):
    familyFiles = []
    for root, dirs, files in os.walk(familiesFolder):
        for fileName in files:
            if (string.lower(os.path.splitext(fileName)[1]) in ['.csv']) and (fileName[:7] == "STRUCT_") :
                familyFiles.append(os.path.join(root, fileName))
    #print "found %s files in %s folders"%(len(familyFiles), len(dirs))
    print "found %s family files"%(len(familyFiles))
    return familyFiles

def extractAttr(directory, structFileName):
    paramFileName = os.path.join(os.path.dirname(structFileName), "PARAM_" + os.path.basename(structFileName)[7:])
    if(not os.path.isfile(paramFileName)):
        print "[NOTICE]skipping %s since %s does not exists"%(structFileName, paramFileName)
    else:
        methodFileName = ''
        paramReader = codecs.open(paramFileName, 'r', 'utf8').readlines()
        for currentLine in paramReader:
            currentLine = currentLine.split(";")
            if currentLine[0] == "METHOD":
                if( (currentLine[1][0] != '*') and (currentLine[1][0] != '+') ):
                    methodFileName = currentLine[1]
                    break

        structReader = codecs.open(structFileName, 'r', 'utf8').readlines()
        attributes = []
        for currentLine in structReader:
            currentLine = currentLine.split(";")
            if currentLine[0] == "ATTR":
                attributes.append(currentLine[1].lower())
            if currentLine[0] == "PARAM":
                attributes.append(currentLine[1].lower())
            if currentLine[0] == "METHOD":
                if( (currentLine[1][0] != '*') and (currentLine[1][0] != '+') ):
                    if(methodFileName != ""):
                        print "[ERROR]duplicate method declaration for %s | %s"%(structFileName, paramFileName)
                        break
                    methodFileName = currentLine[1]

        if(methodFileName == ''):
            #TODO: add verbosity usage
            print "[NOTICE]skipping %s | %s since there is no method declared"%(paramFileName, structFileName)
        else:
            methodFileName = os.path.join(directory, methodFileName)
            if(not os.path.isfile(methodFileName)):
                print "\tmethod file %s for %s does not exists"%(methodFileName, paramFileName)
            else:
                print "working on %s for %s | %s"%(methodFileName, structFileName, paramFileName)
                methodFile = codecs.open(methodFileName, 'r', 'utf8')
                methodContent = []
                modeInAttr = False
                injectAttr = True
                for currentContent in methodFile.readlines():
                    if currentContent.find("/**ATTR**/") >= 0:
                        modeInAttr = not(modeInAttr)
                        if modeInAttr :
                            if injectAttr:
                                #opening attr tag
                                methodContent.append(currentContent)
                                for currentAttr in attributes:
                                    methodContent.append("    const %s = '%s';\n"%(currentAttr, currentAttr))
                                #prevent injection from happening twice
                                injectAttr = False
                        else :
                            #closing attr tag
                            methodContent.append(currentContent)
                    else :
                        methodContent.append(currentContent)
                methodFile.close()

                if(modeInAttr):
                    print "[ERROR] %s not written, there seems to be a structure error."%(methodFileName)
                else:
                    if (len(methodContent) > 0) and not(modeInAttr):
                        methodFile = codecs.open(methodFileName, 'w', 'utf8')
                        methodFile.writelines(methodContent)
                        methodFile.close()
                        print "\t%s attributes written in %s for %s"%(len(attributes), os.path.basename(methodFileName), os.path.basename(structFileName))

def main():
    args = parseOptions()
    for fileName in args.csvFiles:
        extractAttr(args.familiesFolder, fileName)

if __name__ == "__main__":
    main()