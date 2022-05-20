#! /bin/bash

# Script to sync things from the DAQ machine to the Analysis machine
# Insert into crontab like:
# */5 * * * * source /path/to/sync_raw_data.sh &> /path/to/sync_raw_data.log

rsync -avh --progress pioneer-daq:/data/ /data/
