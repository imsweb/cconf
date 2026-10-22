from cconf import Secret, config

HOSTNAME = config("HOSTNAME")
USERNAME = config("USERNAME")
PASSWORD = config("PASSWORD", sensitive=True, cast=Secret)
DEBUG = config("DEBUG", "false", cast=bool)
API_KEY = config("API_KEY", sensitive=True, cast=Secret)
