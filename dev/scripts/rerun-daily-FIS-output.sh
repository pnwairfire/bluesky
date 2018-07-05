#!/usr/bin/env bash

if [ $# -lt 5 ]
  then
    echo ""
    echo "Usage: $0 <host_output_root_dir> <domain> <init_time> <mount_local_code> <module_1> [optional_module_2] [...]"
    echo ""
    echo "Examples:"
    echo "  $0 $HOME/code/pnwairfire-bluesky/tmp/ PNW4km-FireSpider-FIS 2018062100 TRUE visualization"
    echo "  $0 /data/bluesky-pipeline/output/standard/PNW4km-FS-FIS/ PNW4km-FireSpider-FIS 2018062100 FALSE dispersion visualization"
    echo ""
    exit 1
fi

HOST_OUTPUT_ROOT_DIR=$(echo $1 | sed 's:/*$::')
DOMAIN=$2
INIT_TIME=$3
MOUNT_LOCAL=$4

MODULES_STR=""
while [ $# -gt 4 ]
do
  MODULES_STR=$MODULES_STR' '$5
  shift
done

echo "Output root dir: $HOST_OUTPUT_ROOT_DIR"
echo "Domain: $DOMAIN"
echo "Init time: $INIT_TIME"
echo "Mount local code: $MOUNT_LOCAL"
echo "Modules to run: $MODULES_STR"

OUTPUT_FILE=$HOST_OUTPUT_ROOT_DIR/$INIT_TIME/output.json
INDENTED_OUTPUT_FILE=$HOST_OUTPUT_ROOT_DIR/$INIT_TIME/forecast/output-indented.json
if [ -f $INDENTED_OUTPUT_FILE ]; then
   echo "$INDENTED_OUTPUT_FILE exists."
else
   cat $OUTPUT_FILE |python -m json.tool > $INDENTED_OUTPUT_FILE
fi

BSP_CMD="docker run -ti --rm"
BSP_CMD=$BSP_CMD' -v '$HOST_OUTPUT_ROOT_DIR/$INIT_TIME'/forecast:/data/bluesky-daily/output/'$DOMAIN'/'$INIT_TIME'/'
if [ $MOUNT_LOCAL = 'TRUE' ]; then
    BSP_CMD=$BSP_CMD' -v '$HOME'/code/pnwairfire-bluesky/:/bluesky/'
    BSP_CMD=$BSP_CMD' -v '$HOME'/code/pnwairfire-blueskykml/:/blueskykml/'
    BSP_CMD=$BSP_CMD' -e PYTHONPATH=/bluesky/:/blueskykml/'
    BSP_CMD=$BSP_CMD' -e PATH=/bluesky/bin/:$PATH'
fi

BSP_CMD=$BSP_CMD' -w /bluesky/ bluesky'
BSP_CMD=$BSP_CMD' bsp --log-level=DEBUG'
BSP_CMD=$BSP_CMD' -B statuslogging.enabled=false'
BSP_CMD=$BSP_CMD' -i /data/bluesky-daily/output/'$DOMAIN'/'$INIT_TIME'/output-indented.json'
BSP_CMD=$BSP_CMD' -o /data/bluesky-daily/output/'$DOMAIN'/'$INIT_TIME'/output-rerun.json'
BSP_CMD=$BSP_CMD' '$MODULES_STR

echo "About to run:  $BSP_CMD"

eval $BSP_CMD
