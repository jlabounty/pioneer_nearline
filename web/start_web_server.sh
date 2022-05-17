#!/bin/bash

# */5 * * * * /usr/bin/flock -n /home/daq/labounty/web/plot.lock \
#             source /home/daq/labounty/web/start_web_server.sh > \
#             /home/daq/labounty/web/web_server.log 2>&1

#eval "$(/home/daq/labounty/conda/bin/conda shell.bash hook)"
eval "$(/PATH/TO/bin/conda shell.bash hook)"
export PYTHONPATH="/PATH/TO/CONDA/lib"
export LD_LIBRARY_PATH="/PATH/TO/CONDA/lib:$LD_LIBRARY_PATH"
cd /PATH/TO/pioneer_nearline/WEB

python app.py