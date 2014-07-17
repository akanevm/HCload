#!/bin/sh
git pull
HOST=`hostname`
LOAD_FILE=HCload-$HOST.json
echo $LOAD_FILE
git-commit -m "Updating load stats from $HOST" $LOAD_FILE
git push
