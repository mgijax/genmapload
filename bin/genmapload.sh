#!/bin/sh
#
#  genmapload.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the entire UniProt load process.
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
#      3) Call makeUniProtAssocFile.sh to make an association file
#         from the UniProt input file.
#      4) Call makeMGIMapFile.sh to make an association file from
#         the database.
#      5) Call makeBuckets.sh to bucketize the association files.
#      6) Call makeBucketsDiff.sh to run diff of old/new buckets.
#      7) Call loadBuckets.sh to load associations created by bucketizer.
#      8) Call makeGOAnnot.sh to generate/load marker-to-GO annotations.
#      9) Call makeInterProAnnot.sh to generate/load InterPro vocabulary
#         and marker-to-interpro annotations.
#      10) Call ${MGICACHELOAD}/inferredfrom.csh to refresh the inferred-from cache.
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
# Create/load the new map file.
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Call makeGenMapFile.sh (genmapload.sh)" | tee -a ${LOG}
./makeGenMapFile.sh 2>&1 >> ${LOG}
STAT=$?
checkStatus ${STAT} "makeGenMapFile.sh (genmapload.sh)"

#
# run postload cleanup and email logs
#
shutDown
exit 0
