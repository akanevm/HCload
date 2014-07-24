#!/bin/bash

# Wrapper to start up a Django shell with the HC environment set.
# ARGUMENTS: <app> (the HammerCloud app name)
#            <command> (a Django CLI command, by default shell)

# Setup HammerCloud.
APP=$1
HCDIR=`which $0 | sed 's/\/scripts/ /g' | awk '{print $1}'`
echo $HCDIR
source $HCDIR/scripts/config/config-main.sh $APP

# Launch the Django CLI (remove the app name).
shift
HCAPP=$HCDIR/apps/$APP
echo $HCAPP
SCRIPT=$1
if [ -e $HCAPP/python/scripts/$1 ];
then
   echo "running $HCAPP/python/scripts/$SCRIPT"
   python $HCAPP/python/scripts/$SCIPT ${*:-shell}

elif [ -e $HCAPP/python/scripts/server/$SCRIPT ];
then
   echo "running $HCAPP/python/scripts/server/$SCRIPT"
   python $HCAPP/python/scripts/server/$SCRIPT ${*:-shell}
elif [ -e $HCAPP/python/scripts/submit/$SCRIPT ];
then
   echo "running $HCAPP/python/scripts/submit/$SCRIPT"
   python $HCAPP/python/scripts/submit/$SCRIPT ${*:-shell}
fi
