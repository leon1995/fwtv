import os

try:
    __version__ = os.environ["FWTV_VERSION"]
except KeyError:
    __version__ = "0.0.0"
