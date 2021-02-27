#!/usr/bin/env python3
###############################################################################
# NAME:             Prepare.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Prepares generated HTML files to be built with Middleman.
#
# CREATED:          07/12/2020
#
# LAST EDITED:      02/26/2021
###

import argparse

from bs4 import BeautifulSoup

def getPdfPath(htmlPath):
    """Obtain the path of the PDF from the path of the HTML file"""
    return f'pdf/{htmlPath.replace("html","pdf")}'

def getErbPath(htmlPath):
    """Obtain the path of the ERB file from the path of the HTML file"""
    return f'source/{htmlPath}.erb'

def getPrologue(pageData):
    """Prepare the prologue for the ERB file"""
    return (
        '---\n' +
        '\n'.join([f'{key}: {val}' for key, val in pageData.items()]) + '\n'
        '---\n'
    )

def getRelevantStyle(cssFile):
    """Obtain some relevant CSS styling from the cssFile."""
    output = ''
    for line in cssFile.readlines():
        if '.textcolor-' in line:
            output += line
    return output

def prepareTemplate(inputFile, outputFile, cssFile, pageData):
    """Renders the input file to produce an ERB template"""
    soup = BeautifulSoup(inputFile, 'html.parser')
    if soup.title.text:
        pageData['title'] = soup.title.text
    else:
        raise RuntimeError('No title in the HTML head!')
    pageData['pdfLink'] = f'/{getPdfPath(inputFile.name)}'
    prologue = getPrologue(pageData)

    style = soup.new_tag('style')
    style.string = getRelevantStyle(cssFile)
    outputFile.write(prologue)
    outputFile.write(style.decode(formatter="html"))
    for childElement in soup.find('body').findChildren(recursive=False):
        outputFile.write(childElement.decode(formatter="html"))

def main():
    """Prepares generated HTML files to be build with Middleman"""
    parser = argparse.ArgumentParser()
    parser.add_argument('inputFilename')
    parser.add_argument('cssFilename')
    parser.add_argument('outputFilename')
    parser.add_argument('--page-data', '-d',
                        help=('Additional data for the yaml template header'),
                        default='')
    arguments = parser.parse_args()
    pageData = {}
    if arguments.page_data:
        for entry in arguments.page_data.split(','):
            key, value = entry.split('=')
            pageData[key] = value

    with open(arguments.inputFilename, 'r') as inFile, \
         open(arguments.outputFilename, 'w') as outFile, \
         open(arguments.cssFilename, 'r') as cssFile:
        prepareTemplate(inFile, outFile, cssFile, pageData)

if __name__ == '__main__':
    main()

###############################################################################
