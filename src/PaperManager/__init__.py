import sys

__version__ = "0.0.1.dev1"
__author__ = "Mingze Gao"
__homepage__ = "https://github.com/mgao6767/PaperManager"

if sys.version_info.major < 3 and sys.version_info.minor < 10:
    print("Python3.10 or higher is required.")
    sys.exit(1)
