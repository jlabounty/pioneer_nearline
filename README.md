# pioneer_nearline
Nearline analysis code and web interface for the PIONEER beam test May 2022

In order to set up, please add the following to the crontab of the Nearline machine

```
*/1 * * * * /usr/bin/flock -n /PATH/TO/pioneer_nearline/web/plot.lock bash /PATH/TO/pioneer_nearline/scripts/auto_process.sh > /PATH/TO/pioneer_nearline/analysis/scripts/process_data.log 2>&1
*/1 * * * * /usr/bin/flock -n /PATH/TO/pioneer_nearline/web/plot.lock bash /PATH/TO/pioneer_nearline/web/start_web_server.sh > /PATH/TO/pioneer_nearline/web/web_server.log 2>&1
```