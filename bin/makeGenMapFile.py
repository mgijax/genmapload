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

# file name MGI_MAP_FILE
mgiMapFile = None

# file name NEW_MAP_FILE
newMapFile = None

# file pointer
fpSNPMap = None
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
    global snpMapFile, mgiMapFile, newMapFile
    global fpSNPMap, fpMGIMap, fpNEWMap

    snpMapFile = os.getenv('SNP_MAP_FILE')
    mgiMapFile = os.getenv('MGI_MAP_FILE')
    newMapFile = os.getenv('NEW_MAP_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not snpMapFile:
        print 'Environment variable not set: SNP_MAP_FILE'
        rc = 1

    if not mgiMapFile:
        print 'Environment variable not set: MGI_MAP_FILE'
        rc = 1

    if not newMapFile:
        print 'Environment variable not set: NEW_MAP_FILE'
        rc = 1

    #
    # copy new input file
    #

    try:
        os.system('cp -r ${SNP_DOWNLOAD_FILE} ${INPUTDIR}')
    except:
        print 'Cannot copy the input file: ' + \
              os.environ('SNP_DOWNLOAD_FILE') + ' to ' + os.environ('INPUT_DIR')
        return 1

    #
    # Initialize file pointers.
    #
    fpSNPMap = None
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
    global snpMap

    #
    # Open the map files
    #
    try:
        fpSNPMap = open(snpMapFile, 'r')
    except:
        print 'Cannot open map file: ' + snpMapFile
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

    return 0

#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: close file pointers
# Throws: Nothing
#
def closeFiles():
    global fpSNPMap, fpMGIMap, fpNEWMap

    if fpSNPMap:
        fpSNPMap.close()

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

	# not all of these fields are needed for the interpolation,
	# but are handy for testing/debugging

	(markerKey, symbol, accid, chr, cM, bp) = line.strip().split(TAB)

	# if there is no basepair,
	#     then set this map position to syntenic

	if bp == 'None' or bp <= 0:
	    newCm = '-1.0'

	#
	# if chromosome does not exist in snpMap
	#     then set this map position to syntenic
	#
	# these are "MT", "XY", "Y"
	# note that some of the MT's have genome coordinates
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

