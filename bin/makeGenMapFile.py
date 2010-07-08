#!/usr/local/bin/python
#
#  makeGenMapFile.py
###########################################################################
#
#  Purpose:
#
#      This script will interpolate the SNP/baseline map and the current
#      MGI marker genome coordinates to current map offsets/cM positions
#      (MRK_Offset.offset where source = 0).
#
#  Usage:
#
#      makeGenMapFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	   SNP_MAP_FILE
#	   MIT_MAP_FILE
#          MGI_MAP_FILE
#	   NEW_MAP_FILE
#
#  Inputs:
#
#      - SNP/baseline map ($SNP_MAP_FILE)
#        SNP backbone map from Cox, et.al.
#        One row per SNP which give that SNP's genomic coordinate 
#        along with its position on the female, male, and sex-averaged genetic maps.
#
#        It has the following comma-delimited fields:
#
#        1) SNP id
#           Most of these are RefSNP ids, but there are some other types as well.
#           (Doesn't really matter for our purposes.)
#        2) Chromosome
#           the chromosome 1 - 20. (20 == "X").
#           Note that the SNP map does NOT include chromosome 
#           Y, XY (pseudoutosomal), or MT (mitochondrial).
#	 3) Build 37 genome coordinate for the SNP
#	 4) female cM genetic location (female map)
#	 5) male cM genetic location (male map)
#	 6) average cM genetic location (sex averaged map)
#
#        Sample:
#
#               snpID,chr,build37,fem_cM,mal_cM,ave_cM
#               zero1,1,0,0.000,0.000,0.000
#               rs3683945,1,3187481,1.663,1.521,1.593
#               rs3707673,1,3397474,1.769,1.521,1.648
#               rs6269442,1,3482276,1.769,1.521,1.648
#
#      - MIT map file ($MIT_MAP_FILE)
#
#        1) Marker name 1
#        2) Marker name 2
#        3) Marker name 3
#        4) MGI Marker Accession ID
#        5) MGI Primer Pair ID ==> translate to marker
#        6) Primer 1 sequence
#        7) Primer 2 sequence
#        8) build 37 chromosome
#        9) build 37 bp start
#        10) build 37 bp end
#        11) how mapped
#	 12) status ==> "good"
#	 13) fem_cM
#	 14) mal_cM
#	 15) ave_cM ==> "good" map positions
#	 16) MGI Chromosome
#	 17) MGI cM
#	 18) MGI Symbol
#	 19) Chromosome assigned
#	 20) fem_assigned_cM
#	 21) mal_assigned_cM
#	 22) sexave_assigned_cM ==> other map assignments
#	 23) map position status
#	 24) note
#
#        if field 12 (status) == "good":
#	     position = field 15
#        else ignore
#
#      - MGI map file ($MGI_MAP_FILE)
#	 Current MGI map
#        It has the following tab-delimited fields:
#
#        1) Marker key
#        2) Symbol
#	 3) MGI ID
#        4) Chromosome
#        5) cM (centimorgan) 
#           offset, current map position
#        6) bp (basepair)
#           build 37 genome coordinate (start coordinate)
#
#  Outputs:
#
#	- MRK_Offset file ($NEW_MAP_FILE)
#         BCP file of map positions (MRK_Offset.source = 0)
#         The existing map positions will be deleted and the
#         new map positions inserted into MRK_Offset.
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
#      3) Interpolate
#      4) Create BCP files
#      5) Close files.
#
#  Notes:  None
#
#  06/22/2010    lec
#       - TR 9316/new genetic map
#
###########################################################################

import sys 
import os
import string
import db
import mgi_utils

# file name SNP_MAP_FILE
snpMapFile = None

# file name MIT_MAP_FILE
mitMapFile = None

# file name MGI_MAP_FILE
mgiMapFile = None

# file name NEW_MAP_FILE
newMapFile = None

# file pointer
fpSNPMap = None
fpMITMap = None
fpMGIMap = None
fpNEWMap = None

# the snp map
# key = chromosome
# value = [(bp, fcM, mcM, acM), (bp, fcM, mcM, acM)...]
snpMap = {}
I_BP = 0	# basepair coordiante
I_FCM = 1	# female map coordinate
I_MCM = 2	# male map coordinate
I_ACM = 3	# sex-averaged map coordinate

# the mit map
# key = marker key (field 4)
# value = acM (field 15)
mitMap = {}

# interpolate bp->cM
fromCoord = I_BP
toCoord = I_ACM

# current date
cdate = mgi_utils.date('%m/%d/%Y')

# offset table name
mapSource = 0

# MRK_Offset insert format
insertFormat = '%s\t' + str(mapSource) + '\t%s\t' + cdate + '\t' + cdate + '\n'

COMMA = ','
TAB = '\t'

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: sets the global variables, file pointers, etc.
# Throws: Nothing
#
def initialize():
    global snpMapFile, mitMapFile, mgiMapFile, newMapFile
    global fpSNPMap, fpMITMap, fpMGIMap, fpNEWMap

    snpMapFile = os.getenv('SNP_MAP_FILE')
    mitMapFile = os.getenv('MIT_MAP_FILE')
    mgiMapFile = os.getenv('MGI_MAP_FILE')
    newMapFile = os.getenv('NEW_MAP_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not snpMapFile:
        print 'Environment variable not set: SNP_MAP_FILE'
        rc = 1

    if not mitMapFile:
        print 'Environment variable not set: MIT_MAP_FILE'
        rc = 1

    if not mgiMapFile:
        print 'Environment variable not set: MGI_MAP_FILE'
        rc = 1

    if not newMapFile:
        print 'Environment variable not set: NEW_MAP_FILE'
        rc = 1

    #
    # Initialize file pointers.
    #
    fpSNPMap = None
    fpMITMap = None
    fpMGIMap = None
    fpNEWMap = None

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
    global fpSNPMap, fpMGIMap, fpNEWMap
    global snpMap, mitMap

    #
    # Open the map files
    #
    try:
        fpSNPMap = open(snpMapFile, 'r')
    except:
        print 'Cannot open map file: ' + snpMapFile
        return 1

    try:
        fpMITMap = open(mitMapFile, 'r')
    except:
        print 'Cannot open map file: ' + mitMapFile
        return 1

    try:
        fpMGIMap = open(mgiMapFile, 'r')
    except:
        print 'Cannot open map file: ' + mgiMapFile
        return 1

    try:
        fpNEWMap = open(newMapFile, 'w')
    except:
        print 'Cannot open map file: ' + newMapFile
        return 1

    #
    # Create snpMap lookup
    #
    lineNum = 0
    for line in fpSNPMap.readlines():

	lineNum = lineNum + 1

	# skip header line
	if lineNum == 1:
	    continue
	    
        (snpid, chr, bp, fcM, mcM, acM) = line.split(COMMA)

	if chr == '20':
	    mcM = acM = fcM

	key = chr
	value = (float(bp), float(fcM), float(mcM), float(acM.strip()))

	if not snpMap.has_key(key):
	    snpMap[key] = []
	snpMap[key].append(value)

    #
    # Create mitMap lookup
    #

    #
    # create a mitMarker lookup
    # read in all of the DMit markers in the database
    # key = marker accession id
    # value = marker key
    #

    results = db.sql('''
	  select a.accID, m._Marker_key, m.symbol
	  from MRK_Marker m, ACC_Accession a
	  where m._Organism_key = 1
	  and m._Marker_Status_key in (1,3)
	  and m.symbol like 'd%mit%'
	  and m._Marker_key = a._Object_key
	  and a._MGIType_key = 2
	  and a._LogicalDB_key = 1
	  and a.prefixPart = "MGI:"
	  ''', 'auto')

    mitMarker = {}
    for r in results:
        key = r['accID']
	value = r['_Marker_key']
        if not mitMarker.has_key(key):
            mitMarker[key] = []
	#else:
	#    print key, value
        mitMarker[key].append(value)

    #
    # for each DMit marker in the input file
    #   if status != "good", skip
    #   if the marker can be found in the mitMarker lookup
    #   then add the marker to the mitMap lookup
    #

    lineNum = 0
    for line in fpMITMap.readlines():

	lineNum = lineNum + 1

	# skip header line
	if lineNum == 1:
	    continue
	    
        tokens = line.split(TAB)

	markerID = tokens[3]
	mitStatus = tokens[11]
	acM = tokens[14]

	# skip if status is not "good"

	if mitStatus != "good":
            #print 'status != good ', markerID, mitStatus
	    continue

	# duplicate markers should have the same acM
	# so we just grap the first one we find

	if mitMarker.has_key(markerID):
	    for key in mitMarker[markerID]:
	        value = acM
		if value == "":
	            #print 'acM is blank', markerID
		    continue
	        if not mitMap.has_key(key):
	            mitMap[key] = []
	            mitMap[key].append(value)
	        #else:
		#    print mitMarker[markerID], markerID, value
		#    print mitMap[key]
	#else:
	#    print 'cannot find marker in MGD: ', markerID

    return 0

#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: close file pointers
# Throws: Nothing
#
def closeFiles():
    global fpSNPMap, fpMITMap, fpMGIMap, fpNEWMap

    if fpSNPMap:
        fpSNPMap.close()

    if fpMITMap:
        fpMITMap.close()

    if fpMGIMap:
        fpMGIMap.close()

    if fpNEWMap:
        fpNEWMap.close()

    db.useOneConnection(0)

    return 0

#
# Purpose: Performs a binary search of the SNP (by position)
# Returns: the SNP interval containing the given position
#    imax is an index within snpMap for a given chromosome
#    the position argument (pos) is in the interval defined by the SNP 
#    at imax and the one at imaX+1.
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
# Args:
#   s           marker value = (bp, fcM, mcM, acM)
#   pos         (numeric) The position to locate.
#   fromCoord   (integer) The column number in the SNP table to search in.
#

def bsearch(s, pos, fromCoord):

    imin = 0
    imax = len(s) - 1

    # binary seach loop

    while imin <= imax:

	# check the middle item
        imid = (imin + imax)/2
        ival = s[imid][fromCoord]

        if pos > ival:
	    # too big, check second  half of list
            imin = imid + 1

        elif pos <= ival:
	    # too little, check first half of list
            imax = imid - 1

    return imax

#
# Purpose: Converts (via interpolation) one type of coordinate to another
# Returns: the new map position
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
# Args:
#   chr       (integer) chromosome number (1-20)
#   pos       (numeric) position to convert
#   fromCoord (integer) column in which to search for pos
#   toCoord   (integer) column to interpolate to get answer
#

def convert(chr, pos, fromCoord = I_BP, toCoord = I_ACM):

    s = snpMap[chr]
    i = bsearch(s, pos, fromCoord)

    if i == len(s) - 1:
	x = float(s[i][toCoord])
	y = float(s[i][fromCoord])
	pos = float(pos)
	pos2 = float(pos * x)/y

        if toCoord == I_BP:
            pos2 = int(pos2)
    else:

        from1 = s[i][fromCoord]
        from2 = s[i+1][fromCoord]
        f = float(pos - from1)/(from2 - from1)
        to1 = s[i][toCoord]
        to2 = s[i+1][toCoord]
        pos2 = to1 + f*(to2-to1)
        if toCoord == I_BP:
            pos2 = int(pos2)

    return pos2

#
# Purpose: Generate the map by interpolating
#          the SNP map and the MGI map.
# Returns: 0
# Assumes: Nothing
# Effects: creates the map file
# Throws: Nothing
#
def genMap():

    #
    # for each marker found in mgd...
    #

    for line in fpMGIMap.readlines():

	# we can remove symbol, accid, cM
	# there must have been put in for testing
	# they are not used for anything, really
	(markerKey, symbol, accid, chr, cM, bp) = line.strip().split(TAB)

	# if marker is annotated to a mit marker
	#     then use the mit map

	if mitMap.has_key(int(markerKey)):
	    newCm = mitMap[int(markerKey)][0]

	# if there is no basepair,
	#     then set this map position to syntenic

	elif bp == 'None' or bp <= 0:
	    newCm = '-1.0'

	#
	# if chromosome does not exist in snpMap
	#     then set this map position to syntenic
	# these are "MT", "XY", "Y"
	# and could just be removed from makeMGIMapFile.py
	# but some of the MT's have genome coordinates
	#

	elif not snpMap.has_key(chr):
	    #print 'chromosome not found in snpMap:  ', symbol, chr
	    newCm = '-1.0'

	# for everything else, interpolate the map position

        else:
	    # send convert the chromosome and the bp of the marker
	    newCm = str(convert(chr, float(bp)))

        #print string.join([markerKey, symbol, accid, chr, cM, bp, newCm], TAB)
        fpNEWMap.write(insertFormat % (markerKey, newCm))

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if genMap() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()

sys.exit(0)

