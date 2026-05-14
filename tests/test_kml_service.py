from pathlib import Path

from src.services.kml_service import KmlService


def test_parse_coordinates():
    coords = KmlService._parse_coordinates("-77.0,-12.0,0 -77.1,-12.1,0")
    assert coords == [(-77.0, -12.0), (-77.1, -12.1)]
