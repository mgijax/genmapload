#!/bin/sh
#
#  genmapload.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the entire Genetic Map load process.
#
#  Usage:
#
#      genmapload.sh
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
#      3) Call makeMGIMapFile.sh to create the MGI map file.
#      4) Call makeGenMapFile.sh to create the new genetic map file.
#      5) Call loadGenMapFile.sh to load the genetic map file into the database.
#      6) Call ${MRKCACHELOAD/mrklocation.csh to refresh the marker location cache.
#      7) Run ${QCRPTS}/genmapload/runQC.csh
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
#  Source the DLA library functions.
#

if [ "${DLAJOBSTREAMFUNC}" != "" ]
then
    if [ -r ${DLAJOBSTREAMFUNC} ]
    then
        . ${DLAJOBSTREAMFUNC}
    else
        echo "Cannot source DLA functions script: ${DLAJOBSTREAMFUNC}" | tee -a ${LOG}
        exit 1
    fi
else
    echo "Environment variable DLAJOBSTREAMFUNC has not been defined." | tee -a ${LOG}
    exit 1
fi

#
# createArchive
#
preload ${OUTPUTDIR}

#
# Establish the log file.
#
LOG=${LOG_DIAG}
rm -rf ${LOG}
touch ${LOG}

#
# Create the MGI map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeMGIMapFile.sh (genmapload.sh)" | tee -a ${LOG}
./makeMGIMapFile.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "makeMGIMapFile.sh (genmapload.sh)"

#
# Create the new map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeGenMapFile.sh (genmapload.sh)" | tee -a ${LOG}
./makeGenMapFile.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "makeGenMapFile.sh (genmapload.sh)"

#
# Load the new map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call loadGenMapFile.sh (genmapload.sh)" | tee -a ${LOG}
./loadGenMapFile.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "loadGenMapFile.sh (genmapload.sh)"

#
# Refresh the Marker Location cache
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call ${MRKCACHELOAD/mrklocation.csh (genmapload.sh)" | tee -a ${LOG}
${MRKCACHELOAD}/mrklocation.csh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "mrklocation.csh (genmapload.sh)"

#
# Run reports
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call ${QCRPTS}/genmapload/runQC.csh (genmapload.sh)" | tee -a ${LOG}
${QCRPTS}/genmapload/runQC.csh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "runQC.csh (genmapload.sh)"

#
# run postload cleanup and email logs
#
shutDown
exit 0
