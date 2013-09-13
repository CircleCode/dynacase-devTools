#! /usr/bin/env python
# -*- coding: utf-8 -*-

from string import Template
from collections import OrderedDict
import string
import sys
import os.path
import json
import xml.etree.ElementTree as ET

if sys.version_info < (2, 7):
    raise "must use python 2.7 or greater"
import argparse

def parseOptions():
    argParser = argparse.ArgumentParser(
        description='Generate workflow from graphml file. (requires python >= 2.7)'
    )

    argParser.add_argument('graphmlFile',
        help = 'graphml source file (absolute or relative)')

    argParser.add_argument('familyName',
        help = 'family logical name')

    argParser.add_argument('namespace',
        help = 'target namespace')

    argParser.add_argument('-t', '--targetDir',
        help = 'target directory, where generated files will be placed',
        dest = 'targetDir',
        required = True)

    argParser.add_argument('--prefix',
        help = 'prefix',
        dest = 'prefix',
        default = '')

    argParser.add_argument('--templateDir',
        help = 'templates directory',
        dest = 'templateDir',
        default = os.path.join(os.path.dirname(__file__), 'templates'))

    argParser.add_argument('--localesTargetDir',
        help = 'where to put locales stub file',
        dest = 'localesTargetDir')

    argParser.add_argument('--force',
        help = 'overwrite existing files',
        action = 'store_true',
        dest = 'force',
        default = False)

    args = argParser.parse_args()

    errors = []

    if(not os.path.isfile(args.graphmlFile)):
        errors.append("[ERROR] graphmlFile: %s is not a valid file"%(args.graphmlFile))

    if(not os.path.isdir(args.templateDir)):
        errors.append("[ERROR] templateDir: %s is not a valid directory"%(args.templateDir))

    if(not os.path.isdir(args.targetDir)):
        errors.append("[ERROR] targetDir: %s is not a valid directory"%(args.targetDir))

    tplFile = os.path.join(args.templateDir, "graphml_workflow__class.php.template")
    if(os.path.isfile(tplFile)):
        args.tplFile = tplFile
    else:
        errors.append("[ERROR] tplFile: %s is not found"%(tplFile))

    targetFile = os.path.join(args.targetDir, "%s__WFL_BASE_CLASS.php"%(args.familyName.lower()))
    if(os.path.isfile(targetFile) and not args.force):
        errors.append("[ERROR] targetFile: %s already exists. Use --force to overwrite"%(targetFile))
    else:
        args.targetFile = targetFile

    if(args.localesTargetDir is not None):
        localesTargetFile = os.path.join(args.localesTargetDir, "%s__WFL_BASE_LOCALES.php"%(args.familyName.lower()))
        if(os.path.isfile(localesTargetFile) and not args.force):
            errors.append("[ERROR] targetFile: %s already exists. Use --force to overwrite"%(localesTargetFile))
        else:
            args.localesTargetFile = localesTargetFile

    if(len(errors) > 0):
        for error in errors:
            print(error)
        sys.exit("script aborted due to errors")

    return args

def getStates(tree, namespaces, prefix=''):
    states = []
    propNames = {
        'id' : tree.find("./graphml:key[@for='node'][@attr.name='id']", namespaces).get('id'),
        'activity' : tree.find("./graphml:key[@for='node'][@attr.name='activity']", namespaces).get('id'),
        'name' : tree.find("./graphml:key[@for='node'][@attr.name='name']", namespaces).get('id')
    }
    for node in tree.findall('.//graphml:node', namespaces):
        state = {}
        for propName in propNames.keys():
            propertyNode = node.find(".//graphml:data[@key='%s']"%propNames[propName], namespaces)
            if(propertyNode is not None):
                state[propName] = propertyNode.text

        state['desc'] = ' '.join(node.find(".//y:NodeLabel", namespaces).text.splitlines())

        if(prefix is not ''):
            state['id'] = "%s_%s"%(prefix, state['id'])

        states.append(state)

    # sort states by name
    states.sort(key=lambda state: state['name'])

    return states

def getTransitions(tree, namespaces, prefix=''):
    transitions = []
    nodeNamePropName = tree.find("./graphml:key[@for='node'][@attr.name='name']", namespaces).get('id')
    propNames = {
        'id'   : tree.find("./graphml:key[@for='edge'][@attr.name='id']", namespaces).get('id'),
        'm0'   : tree.find("./graphml:key[@for='edge'][@attr.name='m0']", namespaces).get('id'),
        'm1'   : tree.find("./graphml:key[@for='edge'][@attr.name='m1']", namespaces).get('id'),
        'm2'   : tree.find("./graphml:key[@for='edge'][@attr.name='m2']", namespaces).get('id'),
        'm3'   : tree.find("./graphml:key[@for='edge'][@attr.name='m3']", namespaces).get('id'),
        'ask'  : tree.find("./graphml:key[@for='edge'][@attr.name='ask']", namespaces).get('id'),
        'nr'   : tree.find("./graphml:key[@for='edge'][@attr.name='nr']", namespaces).get('id'),
        'name' : tree.find("./graphml:key[@for='edge'][@attr.name='name']", namespaces).get('id')
    }
    for edge in tree.findall('.//graphml:edge', namespaces):
        transition = {}
        for propName in propNames.keys():
            propertyNode = edge.find(".//graphml:data[@key='%s']"%propNames[propName], namespaces)
            if(propertyNode is not None):
                transition[propName] = propertyNode.text

        transition['desc'] = ' '.join(edge.find(".//y:EdgeLabel", namespaces).text.splitlines())
        transition['e1'] = tree.find(".//graphml:node[@id='%s']/graphml:data[@key='%s']"%(edge.get('source'), nodeNamePropName), namespaces).text
        transition['e2'] = tree.find(".//graphml:node[@id='%s']/graphml:data[@key='%s']"%(edge.get('target'), nodeNamePropName), namespaces).text

        if(prefix is not ''):
            transition['id'] = "%s_%s"%(prefix, transition['id'])

        transitions.append(transition)

    # sort transitions by name
    transitions.sort(key=lambda transition: transition['name'])

    return transitions

def getFirstStateName(tree, namespaces):
    firstStatePropName = tree.find("./graphml:key[@for='graph'][@attr.name='firstState']", namespaces).get('id')
    return tree.find(".//graphml:data[@key='%s']"%firstStatePropName, namespaces).text

def generateConstantsFragment(entries):
    fragmentTplStr = """
    /** $desc */
    const $name = '$id';"""

    fragmentTpl = Template(fragmentTplStr)

    fragments = []
    for entry in entries:
        fragments.append(fragmentTpl.safe_substitute(entry))

    return "".join(fragments)

def generateTransitionsFragment(transitions):
    fragments = []
    transitionFragment =  """
        self::$transitionName => Array($transitionProperties
        )"""
    transitionFragmentTpl = Template(transitionFragment)

    transitionPropertyFragment =  """
            "$propertyName" => $propertyValue"""
    transitionPropertyFragmentTpl = Template(transitionPropertyFragment)

    for transition in transitions:

        transitionProperties = []

        if(('nr' in transition) and ("true" != transition['nr'].lower())):
            propertyValue = "false"
        else:
            propertyValue = "true"
        transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
            'propertyName' : 'nr',
            'propertyValue': propertyValue
        }))

        if('m0' in transition):
            transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
                'propertyName' : 'm0',
                'propertyValue': '"%s"'%transition['m0']
            }))

        if('m1' in transition):
            transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
                'propertyName' : 'm1',
                'propertyValue': '"%s"'%transition['m1']
            }))

        if('m2' in transition):
            transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
                'propertyName' : 'm2',
                'propertyValue': '"%s"'%transition['m2']
            }))

        if('m3' in transition):
            transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
                'propertyName' : 'm3',
                'propertyValue': '"%s"'%transition['m3']
            }))

        if('ask' in transition):
            transitionProperties.append(transitionPropertyFragmentTpl.safe_substitute({
                'propertyName' : 'ask',
                'propertyValue': 'Array("%s")'%'","'.join(json.loads(transition['ask']))
            }))

        fragments.append(transitionFragmentTpl.safe_substitute({
            'transitionName'       : transition['name'],
            'transitionProperties' : ",".join(transitionProperties)
        }))

    return ",".join(fragments)

def generateCycleFragment(transitions):
    fragmentTplStr = """
        Array(
            "e1" => self::$e1,
            "e2" => self::$e2,
            "t"  => self::$name
        )"""

    fragmentTpl = Template(fragmentTplStr)

    fragments = []
    for transition in transitions:
        fragments.append(fragmentTpl.safe_substitute(transition))

    return ",".join(fragments)

def generateMethodFragment(transitions):
    fragments = []
    methods = OrderedDict()

    fragmentTplStr = """
    /**
     * $stage for $name ($desc)
     *    from $e1 to $e2
     */
    public abstract function $method($$nextStep, $$currentStep, $$confirmationMessage='');"""
    preTpl = Template(fragmentTplStr)

    fragmentTplStr = """
    /**
     * $stage for $name ($desc)
     *    from $e1 to $e2
     */
    public abstract function $method($$currentStep, $$previousStep, $$confirmationMessage='');"""
    postTpl = Template(fragmentTplStr)

    for transition in transitions:
        if 'm0' in transition:
            t = transition.copy()
            t['method'] = transition['m0']
            t['stage'] = 'm0'
            methods[transition['m0']] = [
                preTpl,
                t
            ]
        if 'm1' in transition:
            t = transition.copy()
            t['method'] = transition['m1']
            t['stage'] = 'm1'
            methods[transition['m1']] = [
                preTpl,
                t
            ]
        if 'm2' in transition:
            t = transition.copy()
            t['method'] = transition['m2']
            t['stage'] = 'm2'
            methods[transition['m2']] = [
                postTpl,
                t
            ]
        if 'm3' in transition:
            t = transition.copy()
            t['method'] = transition['m3']
            t['stage'] = 'm3'
            methods[transition['m3']] = [
                postTpl,
                t
            ]

    for (template, templateValues) in methods.values():
        fragments.append(template.safe_substitute(templateValues))

    return "\n".join(fragments)

def generateActivitiesFragment(states):
    fragments = []

    activityFragment =  """
            self::$name => '${id}_activity'"""
    activityFragmentTpl = Template(activityFragment)

    for state in states:
        if('activity' in state):
            fragments.append(activityFragmentTpl.safe_substitute(state))

    return ",".join(fragments)

def writeTargetFile(args, states, transitions, firstState):
    templateValues = {
        'namespace'           : string.capwords(args.namespace, '\\'),
        'workflowClass'       : ("%s_wfl_base"%args.familyName).capitalize(),
        'firstState'          : firstState,
        'stateConstants'      : generateConstantsFragment(states),
        'transitionConstants' : generateConstantsFragment(transitions),
        'transitions'         : generateTransitionsFragment(transitions),
        'cycle'               : generateCycleFragment(transitions),
        'abstractMethods'     : generateMethodFragment(transitions),
        'activities'          : generateActivitiesFragment(states),
        'prefix'              : args.prefix if (args.prefix is not '') else '%s_wfl'%args.familyName.lower()
    }

    template = Template(open(args.tplFile).read())
    targetString = template.safe_substitute(templateValues)
    #FIXME: tricky hack for python 2 and 3 compatibility
    if sys.version_info < (2, 8):
        targetString = targetString.encode('utf-8')
    targetFile = open(args.targetFile, 'w')
    targetFile.write(targetString)
    targetFile.close()

def writeLocalesTargetFile(args, states, transitions):
    stateFragmentTplStr = """
    // _COMMENT: (state) $name : $desc
    $i18n = _("$id");"""
    stateFragmentTpl = Template(stateFragmentTplStr)

    activityFragmentTplStr = """
    // _COMMENT: (activity) $name : $activity
    $i18n = _("${id}_activity");"""
    activityFragmentTpl = Template(activityFragmentTplStr)

    transitionFragmentTplStr = """
    // _COMMENT: (transition) $name : $desc
    $i18n = _("$id");"""
    transitionFragmentTpl = Template(transitionFragmentTplStr)

    fragments = ["<?php"]
    for state in states:
        fragments.append(stateFragmentTpl.safe_substitute(state))
        if('activity' in state):
            fragments.append(activityFragmentTpl.safe_substitute(state))
    for transition in transitions:
        fragments.append(transitionFragmentTpl.safe_substitute(transition))

    locales = "".join(fragments)

    #FIXME: tricky hack for python 2 and 3 compatibility
    if sys.version_info < (2, 8):
        locales = locales.encode('utf-8')
    targetFile = open(args.localesTargetFile, 'w')
    targetFile.write(locales)
    targetFile.close()

def main():
    args = parseOptions()

    namespaces = {
        "graphml" : "http://graphml.graphdrawing.org/xmlns",
        "y"       : "http://www.yworks.com/xml/graphml"
    }

    ET.register_namespace("graphml", "http://graphml.graphdrawing.org/xmlns")
    ET.register_namespace("y", "http://www.yworks.com/xml/graphml")
    tree = ET.parse(args.graphmlFile)

    states = getStates(tree, namespaces, args.prefix)
    transitions = getTransitions(tree, namespaces, args.prefix)
    firstStateName = getFirstStateName(tree, namespaces)

    if(args.targetFile is not None):
        writeTargetFile(args, states, transitions, firstStateName)

    if(args.localesTargetFile is not None):
        writeLocalesTargetFile(args, states, transitions)

if __name__ == "__main__":
    main()