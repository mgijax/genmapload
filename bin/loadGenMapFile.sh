#!/bin/sh
#
#  loadGenMapFile.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that
#      loads the genetic map file.
#
#  Usage:
#
#      loadGenMapFile.sh
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
#      3) Call loadGenMapFile.py to create the genetic map file.
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
# Verify that the number of rows in the MGI Map file
# is equal to the number of rows in the new genetic map file
#
if [ `cat ${MGI_MAP_FILE} | wc -l` -ne `cat ${NEW_MAP_FILE} | wc -l` ]
then
    echo "\n**** ERROR ****" >> ${LOG}
    echo "Counts are different:  ${MGI_MAP_FILE}, ${NEW_MAP_FILE}" >> ${LOG}
    exit 1
fi

#
# Call the Python script to create the MGI map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Load the genetic map file (loadGenMapFile.sh)" | tee -a ${LOG}
./loadGenMapFile.py 2>&1 >> ${LOG}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo "Error: Load the genetic map file (loadGenMapFile.sh)" | tee -a ${LOG}
    exit 1
fi

exit 0
