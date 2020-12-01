#!/usr/bin/env python3
import requests
import os
import sys
import time
import logging

from dataclasses import dataclass
from prometheus_client import Counter, Gauge, Summary
from prometheus_client import CollectorRegistry, push_to_gateway
from pythonjsonlogger import jsonlogger


PROMREG = CollectorRegistry()

EXTRACT_TIME = Summary(
    'record_extraction_seconds',
    'Time spent extracting an individual record',
    registry=PROMREG
)
DURATION = Gauge(
    'mining_duration_seconds',
    'Time spent mining data',
    registry=PROMREG

)
DATA_DURATION = Gauge(
    'data_download_seconds',
    'Time spent downloading public data',
    registry=PROMREG

)
RECORD_COUNT = Gauge(
    'record_count_total',
    'total records found',
    registry=PROMREG
)
TELEMETRY_COUNT = Gauge(
    'telemetry_push_attempts_total',
    'total attempts to push vehicle telemetry',
    registry=PROMREG
)
TELEMETRY_DURATION = Summary(
    'telemetry_server_push_seconds',
    'Time spent sending telemetry to the telemetry service',
    registry=PROMREG

)
EXTRACTED_ERROR_RECORDS = Counter(
    'record_extraction_fail_total',
    'Total records that failed to be processed',
    registry=PROMREG

)
SENT_ERROR_RECORDS = Counter(
    'record_sent_fail_total',
    'Total records that failed to be processed',
    registry=PROMREG

)
EXCEPTIONS = Counter(
    'exceptions_total',
    'Total exceptions',
    registry=PROMREG
)
LAST_RUN = Gauge(
    'mining_last_run',
    'The unix timestamp of the last execute',
    registry=PROMREG
)


@dataclass
class Position:
    lon: float
    lat: float

    def to_json(self) -> dict:
        return {
            "longitude": self.lon,
            "latitude": self.lat
        }


@dataclass
class VehicleTelemetry:
    source: str = ""
    trip_id: str = ""
    route_id: str = ""
    vehicle_id: str = ""
    status: str = ""
    timestamp: int = 0
    position: Position = Position(0, 0)

    def to_json(self) -> dict:
        return {
            "source": self.source,
            "tripId": self.trip_id,
            "routeId": self.route_id,
            "objectId": self.vehicle_id,
            "vehicleId": self.vehicle_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "position": self.position.to_json()
        }


@EXCEPTIONS.count_exceptions()
def download_public_data(url: str) -> dict:
    """Download the public data and return as a dictonary."""
    logger = logging.getLogger(__name__)
    start = time.perf_counter()
    try:
        logger.info(f"Getting data from {url}")
        resp = requests.get(url)
        return resp.json()
    except requests.RequestException as ex:
        logger.error(f"could not get data: {ex}")
        return {}
    finally:
        end = time.perf_counter()
        DATA_DURATION.set(end - start)
        logger.info("downloaded data set in %0.2f seconds", (end-start))


@EXCEPTIONS.count_exceptions()
@EXTRACT_TIME.time()
def extract_telemetry(data: dict, source: str) -> VehicleTelemetry:
    """extract the required telemetry from public data."""
    v = VehicleTelemetry()
    v.source = source
    v.trip_id = data["vehicle"]["trip"]["trip_id"]
    v.route_id = data["vehicle"]["trip"]["route_id"]
    v.vehicle_id = data["vehicle"]["vehicle"]["id"]
    v.status = data["vehicle"]["current_status"]
    v.timestamp = data["vehicle"]["timestamp"]
    v.position = Position(
        data["vehicle"]["position"]["longitude"],
        data["vehicle"]["position"]["latitude"]
    )
    RECORD_COUNT.inc()
    return v


@EXCEPTIONS.count_exceptions()
@TELEMETRY_DURATION.time()
def send_telemetry(data: list, server_uri: str) -> int:
    """Send extracted telemetry to the telemetry service.

    Returns the number of records sucessfully sent
    """
    logger = logging.getLogger(__name__)
    count = 0
    for vehicle in data:
        TELEMETRY_COUNT.inc()
        try:
            response = requests.post(server_uri,
                                     json=vehicle.to_json(),
                                     timeout=1
                                     )
            if response.status_code > 299:
                logger.info(response.text)
            response.raise_for_status()
            count += 1
        except requests.RequestException as ex:
            logger.error(
                "error sending telemetry for %s-%s: %s",
                vehicle.source,
                vehicle.vehicle_id,
                ex)
            SENT_ERROR_RECORDS.inc()
            continue
    return count


@EXCEPTIONS.count_exceptions()
def main(data_url, telemetry_server):
    logger = logging.getLogger(__name__)
    LAST_RUN.set(int(time.time()))
    start = time.perf_counter()
    data = download_public_data(data_url)
    vehicles = []

    entities = data.get("entity", [])
    logger.info("found %d vehicles", len(entities))
    if len(entities) < 1:
        raise ValueError("No vehicles found in public data")
    for entity in entities:
        try:
            d = extract_telemetry(entity, "KingCounty")
            vehicles.append(d)
        except Exception:
            EXTRACTED_ERROR_RECORDS.inc()
            continue
    send_telemetry(vehicles, telemetry_server)
    end = time.perf_counter()
    DURATION.set(end - start)
    logger.info("mining run took %0.3f seconds", (end-start))


def setup_logging(log_level):
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)


if __name__ == "__main__":
    setup_logging(log_level='INFO')
    logger = logging.getLogger(__name__)

    try:
        data_url = os.environ['DATA_MINER_URI']
        telemetry_server = os.environ['TELEMETRY_SERVER_URI']
        push_gateway_server = os.environ['PUSH_GATEWAY_URI']
    except KeyError as ex:
        logger.error("%s environment variable not found", ex.args[0])
        sys.exit(1)

    try:
        main(data_url, telemetry_server)
    except Exception as ex:
        logger.error("error running job: %s", ex)

    try:
        push_to_gateway(
            push_gateway_server,
            job='data_miner_king_county',
            registry=PROMREG
        )
        logger.info("metrics sent to push gateway: %s", push_gateway_server)
    except Exception as ex:
        logger.error("could not send telemetry to push gateway: %s", ex)
