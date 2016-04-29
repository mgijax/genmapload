#!/usr/local/bin/python
#
#  checkDMit.py
###########################################################################
#
#  Purpose:
#
#      This script will compare DMit chr/startbp/endbp with MGD coordinates
#
#  Usage:
#
#      checkDMit.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	   MIT_MAP_FILE
#
#  Inputs:
#
#      - MIT map file ($MIT_MAP_FILE)
#
#        4) MGI Marker Accession ID
#	 8) build 37 chromosome
#        9) build 37 bp start
#        10) build 37 bp end
#	 12) status ==> "good"
#	 15) ave_cM ==> "good" map positions
#
#  Outputs:
#
#	- report
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Initialize variables.
#      2) Open files.
#      3) Process data.
#      5) Close files.
#
#  Notes:  None
#
#  07/08/2010    lec
#       - TR 9316/new genetic map
#
###########################################################################

import sys 
import os
import db

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

# file name MIT_MAP_FILE
mitMapFile = None

# file name MIT_DIFF_FILE
mitDiffFile = None

# file pointer
fpMITMap = None
fpMITDiff = None

TAB = '\t'
CRT = '\n'

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: sets the global variables, file pointers, etc.
# Throws: Nothing
#
def initialize():
    global mitMapFile, fpMITMap
    global mitDiffFile, fpMITDiff

    mitMapFile = os.getenv('MIT_MAP_FILE')
    mitDiffFile = os.getenv('MIT_DIFF_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not mitMapFile:
        print 'Environment variable not set: MIT_MAP_FILE'
        rc = 1

    if not mitDiffFile:
        print 'Environment variable not set: MIT_DIFF_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpMITMap = None
    fpMITDiff = None

    db.useOneConnection(1)

    return rc

#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: opens the file pointers and loads the lookup tables
# Throws: Nothing
#
def openFiles():
    global fpMITMap, fpMITDiff

    #
    # Open the map files
    #
    try:
        fpMITMap = open(mitMapFile, 'r')
    except:
        print 'Cannot open map file: ' + mitMapFile
        return 1

    try:
        fpMITDiff = open(mitDiffFile, 'w')
    except:
        print 'Cannot open map file: ' + mitDiffFile
        return 1

    return 0

#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: close file pointers
# Throws: Nothing
#
def closeFiles():
    global fpMITMap, fpMITDiff

    if fpMITMap:
        fpMITMap.close()

    if fpMITDiff:
        fpMITDiff.close()

    db.useOneConnection(0)

    return 0

#
# Purpose: Generate a report of differences between
#          MGI Marker/start/end bp coordinates
#          and MIT/start/end bp coordinates
# Returns: 0
# Assumes: Nothing
# Effects: None
# Throws: Nothing
#
def processReport():

    #
    # create a mitMarker lookup
    # read in all of the DMit markers in the database
    # key = marker accession id
    # value = info
    #

    results = db.sql('''
	  select a.accID, c._Marker_key, m.symbol, m.chromosome,
		 c.startCoordinate as startBP, 
		 c.endCoordinate as endBP
	  from MRK_Location_Cache c, MRK_Marker m, ACC_Accession a
	  where c._Marker_key = m._Marker_key
	  and m._Organism_key = 1
	  and m._Marker_Status_key in (1,3)
	  and lower(m.symbol) like 'd%mit%'
          and m._Marker_key = a._Object_key
          and a._MGIType_key = 2
          and a._LogicalDB_key = 1
          and a.prefixPart = 'MGI:'
	  ''', 'auto')

    mitMarker = {}
    for r in results:
        key = r['accID']
	value = r
	mitMarker[key] = value

    #
    # for each DMit marker in the input file
    #   if status != "good", skip
    #
    #   if the marker can be found in the mitMarker lookup
    #
    #   and the mitMarker.startBP != MIT.startBP
    #   or the mitMarker.endBP != MIT.endBP
    #
    #   the print the record
    #

    lineNum = 0
    for line in fpMITMap.readlines():

	lineNum = lineNum + 1

	# skip header line
	if lineNum == 1:
	    continue
	    
        tokens = line.split(TAB)

	markerID = tokens[3]
	chr = tokens[7]
	startBP = tokens[8]
	endBP = tokens[9]
	mitStatus = tokens[11]
	acM = tokens[14]

	# skip if status is not "good"

	if mitStatus != "good":
	    continue

	if not mitMarker.has_key(markerID):
	    continue

	m = mitMarker[markerID]

	if m['startbp'] == None:
	    msb = 0
        else:
	    msb = int(m['startbp'])

	if m['endbp'] == None:
	    csb = 0
        else:
	    csb = int(m['endbp'])

	#
	# check differences
	#

	if msb != int(startBP) or csb != int(endBP):
	    fpMITDiff.write(markerID + TAB)
	    fpMITDiff.write(m['symbol'] + TAB)
	    fpMITDiff.write(m['chromosome'] + TAB)
	    fpMITDiff.write(str(m['startBP']) + TAB)
	    fpMITDiff.write(str(m['endBP']) + TAB)
	    fpMITDiff.write(chr + TAB)
	    fpMITDiff.write(startBP + TAB)
	    fpMITDiff.write(endBP + TAB)
	    fpMITDiff.write(str(acM) + CRT)

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processReport() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()

sys.exit(0)

