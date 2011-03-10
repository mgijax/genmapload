#!/usr/local/bin/python
#
#  makeMGIMapFile.py
###########################################################################
#
#  Purpose:
#
#      This script will create an output file that contains all of the
#      MGI markers with non-syntenic offsets (offset > 0) or genome hasOffsetinates.
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
#        5) bp (basepair)
#           build 37 genome hasOffsetinate (start hasOffsetinate)
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
#  03/10/2011	lec
#	- TR10622/ignore DNA (_Marker_Type_key = 2)
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

# file name of user, password (for bcp)
user = None
passwordFile = None

#
# markers not "UN"
# markers that are official/interim
# should have offset = >= -1
#
updateSQL = '''update MRK_Offset 
	       set offset = -1
	       from MRK_Offset o, MRK_Marker m
	       where o.source = 0 
	       and o.offset < -1
	       and o._Marker_key = m._Marker_key
	       and m.chromosome not in ("UN")
	       and m._Marker_Status_key in (1,3)
	       '''

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
    global user
    global passwordFile

    mgiMapFile = os.getenv('MGI_MAP_FILE')
    user = os.getenv('MGD_DBUSER')
    passwordFile = os.getenv('MGD_DBPASSWORDFILE')

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

    #
    # Use one connection to the database
    #
    db.set_sqlUser(user)
    db.set_sqlPasswordFromFile(passwordFile)

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
#          non-syntenic offsets (> 0) or basepair hasOffsetinates.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def getMap():

    #
    # set any official/interim offsets = -1
    # if they are currently set to -999
    #
    db.sql(updateSQL, None)

    #
    # Get all official/interim MGI markers
    # ignore DNA segments
    #

    db.sql('''select m._Marker_key, m.symbol, m.chromosome, a.accid
	      into #markers
	      from MRK_Marker m, ACC_Accession a
	      where m._Organism_key = 1
              and m._Marker_Status_key in (1,3)
	      and m.chromosome not in ("UN")
	      and m._Marker_Type_key != 2
              and m._Marker_key = a._Object_key
              and a._MGIType_key = 2
              and a._LogicalDB_key = 1
              and a.preferred = 1
	      and a.prefixPart = "MGI:"
	      ''', None)

    db.sql('create index idx1 on #markers(_Marker_key)', None)

    #
    # copied from mrkcacheload/mrklocation.py
    #

    hasOffset = {}

    #
    # offsets for Marker with MAP_Coord_Feature hasOffsetiantes
    #

    results = db.sql('''select distinct m._Marker_key, startCoordinate = str(f.startCoordinate)
		from #markers m, MAP_Coord_Feature f
		where m._Marker_key = f._Object_key 
		and f._MGIType_key = 2 
		''', 'auto')
    for r in results:
        key = r['_Marker_key']
        value = r['startCoordinate']

    if not hasOffset.has_key(key):
        hasOffset[key] = []
        hasOffset[key].append(value)

    #
    # offsets for Markers w/ Sequence hasOffsetinates
    #

    results = db.sql('''select distinct m._Marker_key, startCoordinate = str(c.startCoordinate)
		from #markers m, SEQ_Marker_Cache mc, SEQ_Coord_Cache c
		where m._Marker_key = mc._Marker_key 
		and mc._Qualifier_key = 615419 
		and mc._Sequence_key = c._Sequence_key
		''', 'auto')
    for r in results:
        key = r['_Marker_key']
        value = r['startCoordinate']

        # only one hasOffsetinate per marker
        if not hasOffset.has_key(key):
            hasOffset[key] = []
            hasOffset[key].append(value)

    #
    # print out the marker/offsets
    #

    results = db.sql('select * from #markers order by _Marker_key', 'auto')

    for r in results:

	key = r['_Marker_key']

	# change "X" to "20"

	chr = r['chromosome']
	if chr == 'X':
	    chr = '20'

	if hasOffset.has_key(key):
	    for c in hasOffset[key]:
                fpMap.write(str(r['_Marker_key']) + '\t' +
                            r['symbol'] + '\t' +
                            r['accid'] + '\t' +
                            chr + '\t' +
		            str(c) + '\n')
	else:
            fpMap.write(str(r['_Marker_key']) + '\t' +
                        r['symbol'] + '\t' +
                        r['accid'] + '\t' +
                        chr + '\t' +
		        'None' + '\n')

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
