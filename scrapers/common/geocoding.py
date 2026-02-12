# Swedish County Coordinates (Central Points)
# Used for geocoding fallback when only county name is available
SWEDISH_COUNTY_COORDS = {
    "Stockholms län": (59.3293, 18.0686),
    "Västra Götalands län": (58.0, 13.0),
    "Skåne län": (55.9, 13.5),
    "Uppsala län": (59.8586, 17.6389),
    "Östergötlands län": (58.4108, 15.6214),
    "Jönköpings län": (57.7826, 14.1618),
    "Kronobergs län": (56.8777, 14.8091),
    "Kalmar län": (56.6634, 16.3567),
    "Gotlands län": (57.6348, 18.2948),
    "Blekinge län": (56.1612, 15.5869),
    "Hallands län": (56.8945, 12.8421),
    "Värmlands län": (59.4021, 13.5115),
    "Örebro län": (59.2753, 15.2134),
    "Västmanlands län": (59.6100, 16.5448),
    "Dalarnas län": (60.6749, 15.0784),
    "Gävleborgs län": (61.0, 16.0),
    "Västernorrlands län": (62.6315, 17.9386),
    "Jämtlands län": (63.1792, 14.6357),
    "Västerbottens län": (64.7507, 18.0542),
    "Norrbottens län": (66.8309, 20.3987),
    "Södermanlands län": (59.0333, 16.75)
}


def get_county_coordinates(county_name: str):
    """Get central coordinates for a Swedish county."""
    return SWEDISH_COUNTY_COORDS.get(county_name)
