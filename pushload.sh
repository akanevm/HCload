#!/bin/sh
cd $(dirname $0)
git pull
HOST=`hostname`
LOAD_FILE=HCload-$HOST.json
echo $LOAD_FILE
git-commit -m "Updating load stats from $HOST" $LOAD_FILE
git push
