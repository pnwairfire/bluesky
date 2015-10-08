if [ $# -ne 2 ]
  then
    echo "Usage: $0 <hostname> <output dir>"
    echo "Ex:  $0 localhost:8888 /tmp/bluesky-web-regressions-output"
    echo ""
    exit 1
fi

BLUESKY_API_HOSTNAME=$1
OUTPUT_DIR=$2
mkdir -p $OUTPUT_DIR

echo "Testing $BLUESKY_API_HOSTNAME"
echo "Outputing to $OUTPUT_DIR"

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
    response=$(curl "$i" --write-out %{http_code} --silent -o $OUTPUT_DIR/ping.json)
    echo $response
done

# response=$(curl --write-out %{http_code} --silent "" -o $OUTPUT_DIR/ping.json)
# echo $response
# curl "http://$BLUESKY_API_HOSTNAME/api/ping/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/available-dates" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/domains/PNW-4km/available-dates/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/available-dates" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/available-dates/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/status" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/status/" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/output" | python -m json.tool
# curl "http://$BLUESKY_API_HOSTNAME/api/v1/run/abc123/output/" | python -m json.tool
# curl -D - "http://$BLUESKY_API_HOSTNAME/api/v1/run/" \
#     -H "Content-Type: application/json" -d '{
#         "modules": ["fuelbeds", "consumption", "emissions"],
#         "fire_information": [
#             {
#                 "id": "SF11C14225236095807750",
#                 "event_id": "SF11E826544",
#                 "name": "Natural Fire near Snoqualmie Pass, WA",
#                 "location": {
#                     "perimeter": {
#                         "type": "MultiPolygon",
#                         "coordinates": [
#                             [
#                                 [
#                                     [-121.4522115, 47.4316976],
#                                     [-121.3990506, 47.4316976],
#                                     [-121.3990506, 47.4099293],
#                                     [-121.4522115, 47.4099293],
#                                     [-121.4522115, 47.4316976]
#                                 ]
#                             ]
#                         ]
#                     },
#                     "ecoregion": "southern",
#                     "utc_offset": "-09:00"
#                 }
#             }
#         ],
#         "config": {
#             "emissions":{
#                 "efs": "feps",
#                 "species": ["PM25"]
#             }
#         }
#     }'

# # or to post data in a file
# curl -D - "http://$BLUESKY_API_HOSTNAME/api/v1/run/" \
#     -H "Content-Type: application/json" \
#     -X POST -d @/path/to/fires.json
