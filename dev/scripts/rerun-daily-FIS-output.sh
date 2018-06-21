#!/usr/bin/env bash

if [ $# -lt 4 ]
  then
    echo ""
    echo "Usage: $0 <output_root_dir> <init_time> <mount_local_code> <module_1> [optional_module_2] [...]"
    echo ""
    echo "Examples:"
    echo "  $0 $HOME/code/pnwairfire-bluesky/tmp/ 2018062100 TRUE visualization"
    echo "  $0 /data/bluesky-daily/plumerise/PNW4km-FireSpider-FIS/ 2018062100 FALSE dispersion visualization"
    echo ""
    exit 1
fi

OUTPUT_ROOT_DIR=$(echo $1 | sed 's:/*$::')
INIT_TIME=$2
MOUNT_LOCAL=$3

MODULES_STR=""
while [ $# -gt 3 ]
do
  MODULES_STR=$MODULES_STR' '$4
  shift
done

echo "Output root dir: $OUTPUT_ROOT_DIR"
echo "Init time: $INIT_TIME"
echo "Mount local code: $MOUNT_LOCAL"
echo "Modules to run: $MODULES_STR"

OUTPUT_FILE=$HOME/code/pnwairfire-bluesky/tmp/$INIT_TIME/output.json
INDENTED_OUTPUT_FILE=$HOME/code/pnwairfire-bluesky/tmp/$INIT_TIME/output-indented.json
if [ -f $INDENTED_OUTPUT_FILE ]; then
   echo "$INDENTED_OUTPUT_FILE exists."
else
   cat $OUTPUT_FILE |python -m json.tool > $INDENTED_OUTPUT_FILE
fi


BSP_CMD="docker run -ti --rm"
BSP_CMD=$BSP_CMD' -v '$OUTPUT_ROOT_DIR/$INIT_TIME'/forecast:/data/bluesky-daily/output/PNW4km-FireSpider-FIS/'$INIT_TIME'/'
if [ $MOUNT_LOCAL = 'TRUE' ]; then
    BSP_CMD=$BSP_CMD' -v '$HOME'/code/pnwairfire-bluesky/:/bluesky/'
    BSP_CMD=$BSP_CMD' -v '$HOME'/code/pnwairfire-blueskykml/:/blueskykml/'
    BSP_CMD=$BSP_CMD' -e PYTHONPATH=/bluesky/:/blueskykml/'
    BSP_CMD=$BSP_CMD' -e PATH=/bluesky/bin/:$PATH'
fi

BSP_CMD=$BSP_CMD' -w /bluesky/ bluesky'
BSP_CMD=$BSP_CMD' bsp --log-level=DEBUG'
BSP_CMD=$BSP_CMD' -B statuslogging.enabled=false'
BSP_CMD=$BSP_CMD' -i /bluesky/tmp/'$INIT_TIME'/output-indented.json'
BSP_CMD=$BSP_CMD' -o /bluesky/tmp/'$INIT_TIME'/output-rerun.json'
BSP_CMD=$BSP_CMD' '$MODULES_STR

echo "About to run:  $BSP_CMD"

$BSP_CMD