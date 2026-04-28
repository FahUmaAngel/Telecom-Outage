from enum import Enum

class OperatorName(str, Enum):
    TELIA = "telia"
    LYCAMOBILE = "lycamobile"
    TRE = "tre"
    TELE2 = "tele2"

class LocationType(str, Enum):
    LAN = "lan"
    CITY = "city"

class OutageStatus(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    INVESTIGATING = "investigating"

class QualityIssue(str, Enum):
    MISSING_COORDS = "missing_coords"
    MISSING_END_DATE = "missing_end_date"
