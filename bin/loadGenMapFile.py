#!/usr/local/bin/python
#
#  loadGenMapFile.py
###########################################################################
#
#  Purpose:
#
#      This script will delete/load the map offsets/cM positions into the database
#      (MRK_Offset.offset where source = 0).
#
#  Usage:
#
#      loadGenMapFile.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	   NEW_MAP_FILE
#	   LOG_DIAG
#	   MGD_DBPASSWORDFILE
#
#  Input:
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
#      2) Load BCP files
#
#  Notes:  None
#
#  03/10/2011	lec
#	- TR10622/ignore DNA-MIT markers (symbol like 'd%mit%')
#
#  06/22/2010    lec
#       - TR 9316/new genetic map
#
###########################################################################

import sys 
import os
import db

# file name NEW_MAP_FILE
newMapFile = None

# file name of diagnostic file (LOG_DIAG)
diagFile = None

# file name of user, password (for bcp)
user = None
passwordFile = None

#
# delete existing map positions
# where offset is -1 (syntenic) or >0 (positive offset)
# and marker status is official/inferred (1,3)
# 
# markers that are withdrawn (marker status = 2) 
# or are UN/-999
# are kept in source = 0 as "history"
# that is, their offset values are not changed/refreshed
#
# ignore DNA segments
#

tableName = 'MRK_Offset'

deleteSQL = '''delete MRK_Offset 
	       from MRK_Offset o, MRK_Marker m
	       where o.source = 0 
	       and o.offset >= -1
	       and o._Marker_key = m._Marker_key
	       and m._Marker_Status_key in (1,3)
	       and m.symbol not like 'd%mit%'
	       '''

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: sets the global variables, file pointers, etc.
# Throws: Nothing
#
def initialize():
    global newMapFile
    global diagFile
    global user
    global passwordFile

    newMapFile = os.getenv('NEW_MAP_FILE')
    diagFile = os.getenv('LOG_DIAG')
    user = os.getenv('MGD_DBUSER')
    passwordFile = os.getenv('MGD_DBPASSWORDFILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not newMapFile:
        print 'Environment variable not set: NEW_MAP_FILE'
        rc = 1

    if not diagFile:
        print 'Environment variable not set: LOG_DIAG'
        rc = 1

    if not passwordFile:
        print 'Environment variable not set: MGD_DBPASSWORDFILE'
        rc = 1

    #
    # Use one connection to the database
    #
    db.set_sqlUser(user)
    db.set_sqlPasswordFromFile(passwordFile)

    return rc

#
# Purpose: Delete existing map positions/bcp in the new map positions
# Returns: 0
# Assumes: Nothing
# Effects: Delete existing map positions/bcp in the new map positions
# Throws: Nothing
#
def bcpFiles():

    db.sql(deleteSQL, None)

    bcpMap = 'cat %s | bcp %s..%s in %s -c -t\"\t" -e %s -S%s -U%s > %s' \
		% (passwordFile, db.get_sqlDatabase(), \
	   	tableName, newMapFile, diagFile, db.get_sqlServer(), db.get_sqlUser(), diagFile)

    #print bcpMap
    os.system(bcpMap)

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if bcpFiles() != 0:
    sys.exit(1)

sys.exit(0)

