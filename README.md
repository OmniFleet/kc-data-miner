# data-miner

Data miner is a job that collects vehicle telemetry from the King County
public APIs to ingest into our telemetry service API.

The data miner runs as a batch job that pulls down the public data, processes
it and then sends off the data to the ingest service.  This utility is ideal
to run as a kubernetes cron job.


## The Data

data-miner pulls the [Enhanced GTFS-RT](https://s3.amazonaws.com/kcm-alerts-realtime-prod/vehiclepositions_enhanced.json)
feed for king county and extracts the following information for ingest

```json
{
  "id": "{source}-{vehicleId}",
  "tripId": "49195225",
  "routeId": "100001",
  "vehicleId": "4350",
  "currentPosition": {
    "latitude": 47.62504,
    "longitude": -122.3567,
  },
  "status": "IN_TRANSIT_TO",
  "timestamp": 1606772228
}
```


