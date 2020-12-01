import pytest

from miner import VehicleTelemetry, Position


@pytest.fixture
def vehicle():
    v = VehicleTelemetry()
    v.source = "testing"
    v.trip_id = "1"
    v.route_id = "1"
    v.vehicle_id = "1"
    v.status = "tesitng"
    v.timestamp = 123456
    v.position = Position(12345, -12345)
    return v


@pytest.fixture
def vehicle_data():
    return {
        "header": {
            "gtfs_realtime_version": "2.0",
            "incrementality": 0,
            "timestamp": 1606866702
        },
        "entity": [
            {
                "id": "1606866702_4377",
                "vehicle": {
                    "trip": {
                        "trip_id": "49195257",
                        "direction_id": 0,
                        "route_id": "100001",
                        "start_date": "20201201",
                        "schedule_relationship": "SCHEDULED"
                    },
                    "vehicle": {
                        "id": "4377",
                        "label": "4377"
                    },
                    "position": {
                        "latitude": 47.64533,
                        "longitude": -122.369377
                    },
                    "current_stop_sequence": 228,
                    "stop_id": "2010",
                    "current_status": "IN_TRANSIT_TO",
                    "block_id": "5890400",
                    "timestamp": 1606866670
                }
            },
        ]
    }
