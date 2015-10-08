if [ $# -lt 1 ] || [ $# -gt 2 ]
  then
    echo "Usage: $0 <hostname> [response output file]"
    echo "Ex:  $0 localhost:8888 /tmp/web-regression-out"
    echo ""
    exit 1
fi

BLUESKY_API_HOSTNAME=$1
if [ $# -eq 2 ]
  then
    OUTPUT_FILE=$2
else
    OUTPUT_FILE=/dev/null
fi

echo "Testing $BLUESKY_API_HOSTNAME"
echo "Outputing to $OUTPUT_FILE"

echo -n "" > $OUTPUT_FILE

GET_URLS=(
    http://$BLUESKY_API_HOSTNAME/api/ping
    http://$BLUESKY_API_HOSTNAME/api/ping/
    http://$BLUESKY_API_HOSTNAME/api/v1/domains
    http://$BLUESKY_API_HOSTNAME/api/v1/domains/
    http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km
    http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/
    http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/available-dates
    http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/available-dates/
    http://$BLUESKY_API_HOSTNAME/api/v1/available-dates
    http://$BLUESKY_API_HOSTNAME/api/v1/available-dates/
    http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/status
    http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/status/
    http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/output
    http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/output/
)
for i in "${GET_URLS[@]}"
  do
    echo -n "Testing $i ... "
    echo -n "$i - " >> $OUTPUT_FILE
    response=$(curl "$i" --write-out %{http_code} --silent >> "$OUTPUT_FILE")
    echo "" >> $OUTPUT_FILE
    echo $response
done

echo -n "Testing http://$BLUESKY_API_HOSTNAME/api/v1/run/ ... "
echo -n "http://$BLUESKY_API_HOSTNAME/api/v1/run/ - " >> $OUTPUT_FILE
response=$(curl "http://$BLUESKY_API_HOSTNAME/api/v1/run/" --write-out %{http_code} --silent  -H "Content-Type: application/json" -d '{
        "modules": ["fuelbeds", "consumption", "emissions"],
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "perimeter": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [-121.4522115, 47.4316976],
                                    [-121.3990506, 47.4316976],
                                    [-121.3990506, 47.4099293],
                                    [-121.4522115, 47.4099293],
                                    [-121.4522115, 47.4316976]
                                ]
                            ]
                        ]
                    },
                    "ecoregion": "southern",
                    "utc_offset": "-09:00"
                }
            }
        ],
        "config": {
            "emissions":{
                "efs": "feps",
                "species": ["PM25"]
            }
        }
    }' >> "$OUTPUT_FILE")
echo "" >> $OUTPUT_FILE
echo $response

# to post data in a file
# curl -D - "http://$BLUESKY_API_HOSTNAME/api/v1/run/" \
#     -H "Content-Type: application/json" \
#     -X POST -d @/path/to/fires.json
