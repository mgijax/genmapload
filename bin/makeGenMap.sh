#!/bin/sh
#
#  makeMGIMapFile.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that
#
#  Usage:
#
#      makeMGIMapFile.sh
#
#  Env Vars:
#
#      See the configuration file (genmapload.config)
#
#  Inputs:  None
#
#  Outputs:
#
#      - Log file (${LOG_DIAG})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal error occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Source the configuration file to establish the environment.
#      2) Establish the log file.
#      3) Call makeMGIMapFile.py to create the MGD map file.
#
#  Notes:  None
#
###########################################################################

cd `dirname $0`

CONFIG=genmapload.config

#
# Make sure the configuration file exists and source it.
#
if [ -f ../${CONFIG} ]
then
    . ../${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# Establish the log file.
#
LOG=${LOG_DIAG}

#
# Call the Python script to create the MGI map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Create the MGI map file (makeMGIMapFile.sh)" | tee -a ${LOG}
#./makeMGIMapFile.py 2>&1 >> ${LOG}
./makeMGIMapFile.py
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Create the MGI map file (makeMGIMapFile.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
