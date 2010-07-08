#!/usr/local/bin/python
#
#  makeMGIMapFile.py
###########################################################################
#
#  Purpose:
#
#      This script will create an output file that contains all of the
#      MGI markers with non-syntenic offsets (offset > 0) or genome coordinates.
#
#  Usage:
#
#      makeMGIMapFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          MGI_MAP_FILE
#
#  Inputs:
#
#	MGD database
#
#  Outputs:
#
#      - MGI map file ($MGI_MAP_FILE)
#        Current MGI map
#        It has the following tab-delimited fields:
#
#        1) Marker key
#        2) Symbol
#        3) MGI ID
#        4) Chromosome
#        5) cM (centimorgan) 
#           offset, current map position
#        6) bp (basepair)
#           build 37 genome coordinate (start coordinate)
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
#      3) Query the database
#      4) Write each MGI ID to the map file.
#      5) Close files.
#
#  Notes:  None
#
#  06/17/2010    lec
#       - TR 9316/new genetic map
#
###########################################################################

import sys 
import os
import db

# file name MGI_MAP_FILE
mgiMapFile = None

# file pointer
fpMap = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global mgiMapFile
    global fpMap

    mgiMapFile = os.getenv('MGI_MAP_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not mgiMapFile:
        print 'Environment variable not set: MGI_MAP_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpMap = None

    return rc

#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpMap

    #
    # Open the association file.
    #
    try:
        fpMap = open(mgiMapFile, 'w')
    except:
        print 'Cannot open association file: ' + mgiMapFile
        return 1

    return 0

#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():
    global fpMap

    if fpMap:
        fpMap.close()

    db.useOneConnection(0)

    return 0

#
# Purpose: Query the database to get the MGI markers that have
#          non-syntenic offsets (> 0) or basepair coordinates.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def getMap():

    #
    # Get all official/interim MGI markers
    #

    results = db.sql('''
           select distinct mc._Marker_key, mm.symbol, a.accid, mc.chromosome, 
		  offset = str(mc.offset), startCoordinate = str(mc.startCoordinate)
           from MRK_Location_Cache mc, MRK_Marker mm, ACC_Accession a
           where mc._Marker_key = mm._Marker_key
           and mm._Marker_Status_key in (1,3)
	   and mm.chromosome not in ("UN")
           and mc._Marker_key = a._Object_key
           and a._MGIType_key = 2
           and a._LogicalDB_key = 1
           and a.preferred = 1
	   and a.prefixPart = "MGI:"
           order by mc.chromosome, mc.offset, mc.startCoordinate
	   ''', 'auto')

    for r in results:

	# change "X" to "20"

	chr = r['chromosome']
	if chr == 'X':
	    chr = '20'

        fpMap.write(str(r['_Marker_key']) + '\t' +
                    r['symbol'] + '\t' +
                    r['accid'] + '\t' +
                    chr + '\t' +
		    str(r['offset']) + '\t' +
		    str(r['startCoordinate']) + '\n')

    return 0

#
#  MAIN
#

db.useOneConnection(1)

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if getMap() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
