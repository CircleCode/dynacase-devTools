#! /usr/bin/env python
# -*- coding: utf-8 -*-

from string import Template
import string
import sys
import os.path

from generateWorkflow import generateWorkflow,getWflMemo

if sys.version_info < (2, 7):
    raise "must use python 2.7 or greater"
import argparse

def parseOptions():
    argParser = argparse.ArgumentParser(
        description='Generate Family files. (requires python >= 2.7)'
    )
    argParser.add_argument('familyName',
        help = 'family logical name')
    argParser.add_argument('namespace',
        help = 'family namespace')
    argParser.add_argument('-f', '--fromName',
        help = 'family parent name',
        dest = 'fromName',
        default = '')
    argParser.add_argument('-p', '--fromClass',
        help = 'family parent class (with namespace)',
        dest = 'fromClass',
        default = '\Dcp\Family\Document')
    argParser.add_argument('--title',
        help = 'family title',
        dest = 'familyTitle')
    argParser.add_argument('--templateDir',
        help = 'templates directory',
        dest = 'templateDir',
        default = os.path.join(os.path.dirname(__file__), 'templates'))
    argParser.add_argument('-t', '--targetDir',
        help = 'target directory, where generated files will be placed',
        dest = 'targetDir',
        required = True)
    argParser.add_argument('--force',
        help = 'overwrite existing files',
        action = 'store_true',
        dest = 'force',
        default = False)
    argParser.add_argument('-w', '--withWorkflow',
        help = 'generate a workflow class for the generated family',
        action = 'store_true',
        dest = 'withWorkflow',
        default = False)
    args = argParser.parse_args()
    if(not args.familyTitle):
        args.familyTitle = "title for %s"%(args.familyName.upper())
    return args

def getStructMemo(templateValues):
    return """
    <process command="./wsh.php --api=importDocuments --file=./@APPNAME@/%s__STRUCT.csv"/>"""%(templateValues['familyName'].lower())

def getParamMemo(templateValues):
    return """
    <process command="./wsh.php --api=importDocuments --file=./@APPNAME@/%s__PARAM.csv"/>"""%(templateValues['familyName'].lower())

def generateFamily(templateValues, args):
    targetsPath ={
        'csvStruct': os.path.join(args.targetDir, "%s__STRUCT.csv"%(args.familyName.lower())),
        'csvParam' : os.path.join(args.targetDir, "%s__PARAM.csv"%(args.familyName.lower())),
        'class': os.path.join(args.targetDir, "%s__CLASS.php"%(args.familyName.lower()))
    }

    if(not args.force):
        overwrittenFiles = 0
        for targetPath in targetsPath:
            if(os.path.exists(targetsPath[targetPath])):
                overwrittenFiles += 1
                print "existingt file %s would be overwritten. please use --force to allow this"%(targetsPath[targetPath])
        if(overwrittenFiles > 0):
            raise NameError("overwriting %s files"%(overwrittenFiles))

    templateFilesPath ={
        'csvStruct': os.path.join(args.templateDir, "family__STRUCT.csv.template"),
        'csvParam' : os.path.join(args.templateDir, "family__PARAM.csv.template"),
        'class': os.path.join(args.templateDir, "family.php.template")
    }

    templates = {}
    for fileDesignation in templateFilesPath:
        templates[fileDesignation] = Template(open(templateFilesPath[fileDesignation]).read())

    for target in targetsPath:
        if templateFilesPath.has_key(target):
            template = Template(open(templateFilesPath[target]).read())
            targetString = template.safe_substitute(templateValues)
            targetFile = open(targetsPath[target], 'w')
            targetFile.write(targetString)
            targetFile.close()
        else:
            print "no template found for %s"%(target)

def main():
    args = parseOptions()

    templateValues = {
        'familyTitle'   : args.familyTitle,
        'familyIcon'    : "%s.png"%(args.familyName.lower()),
        'familyMethod'  : "Method.%s.php"%(args.familyName.lower()),
        'familyDFLID'   : "FLD_%s"%(args.familyName.upper()),
        'familyName'    : args.familyName.upper(),
        'familyClass'   : args.familyName.capitalize(),
        'fromName'      : args.fromName.upper(),
        'fromClass'     : args.fromClass,
        'namespace'     : string.capwords(args.namespace, '\\')
    }

    templateValues['namespaceClass'] = "%s\\%s"%(templateValues['namespace'], templateValues['familyClass'])

    try:
        generateFamily(templateValues, args)
        if(args.withWorkflow):
            generateWorkflow(templateValues, args)
        print(getStructMemo(templateValues))
        if(args.withWorkflow):
            print(getWflMemo(templateValues))
        print(getParamMemo(templateValues))
    except NameError:
        return

if __name__ == "__main__":
    main()
    print ""
