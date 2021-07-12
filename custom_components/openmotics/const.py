"""Constants for OpenMotics integration."""
# Base component constants
NAME = "OpenMotics Integration"
ATTR_MANUFACTURER = "OpenMotics"
DOMAIN = "openmotics"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/openmotics/home-assistant/issues"

NOT_IN_USE = "NOT_IN_USE"

"""
The state of a light is refreshed every 30 seconds (more or less).
Setting the interval between updates to 30 seconds was just a little bit
to late. 28 seconds is better.
"""
# MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)
MIN_TIME_BETWEEN_UPDATES = 28  # seconds

DEFAULT_HOST = 'cloud.openmotics.com'
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False

"""
Get a list of all modules attached and registered with the master.
:returns:
    'output': list of module types (O,R,D) and
    'input': list of input module types (I,T,L).
"""
OPENMOTICS_OUTPUT_TYPES = ['O', 'R', 'D']
OPENMOTICS_INPUT_TYPES = ['I', 'T', 'L']

"""
https://wiki.openmotics.com/index.php/Modules
"""
OPENMOTICS_OUTPUT_TYPE_TO_NAME = {
    0: 'outlet',
    1: 'valve',
    2: 'alarm',
    3: 'appliance',
    4: 'pump',
    5: 'hvac',
    6: 'generic',
    7: 'motor',
    8: 'ventilation',
    255: 'light'
}

OPENMOTICS_MODULE_TYPE_TO_NAME = {
    'O': 'Output',
    'R': 'Roller',  # Also known as Shutter
    'D': 'Dimmer',
    'I': 'Input',
    'T': 'Temperature',
    'L': 'Unknown'
}

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
LIGHT = "light"
SWITCH = "switch"
COVER = "cover"
SCENE = "scene"
#SENSOR = "sensor"
#SWITCH = "switch"
PLATFORMS = [LIGHT, SWITCH, COVER, SCENE]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
#CONF_CLIENT_ID: "client_id"
#CONF_CLIENT_SECRET: "client_secret"

# Defaults
DEFAULT_NAME = DOMAIN

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
