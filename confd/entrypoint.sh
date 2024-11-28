#!/bin/sh

# echo "Start up confd to fetch config from xmate"
/etc/confd/confd

python /app/metagpt/app.py


#work_dir="/app"
#cfg="${work_dir}/config.ini"
#if [ -e ${cfg} ];then
#  echo "Find app's config from xmate: ${cfg}"
#  python /app/app.py
#else
#  echo "Confd load config failed, skip to start app"
#fi
