To install the script that gather the load stats and submit 
them to the couchdb server please run the following commands:

- cp ./run-python-action.sh /data/hc/scripts/config/
- cp ./get_load_stats.py  /data/hc/apps/cms/python/scripts/submit/

Add the following cronjob:
# Check machine load
1-59/10 * * * * /data/hc/scripts/config/run-python-action.sh cms get_load_stats.py -j /root/HCload/HCload-hammercloud-ai-15.json &> /data/hc/apps/cms/logs/get_load_stats.log

