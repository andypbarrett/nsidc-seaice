import os

from .constants import SEA_ICE_BASE_DIR

DATA_STORE_BASE_DIRECTORY = os.path.join(SEA_ICE_BASE_DIR, 'datastore/')

DAILY_DATA_STORE_PATH = os.path.join(DATA_STORE_BASE_DIRECTORY, 'daily.p')
MONTHLY_DATA_STORE_PATH = os.path.join(DATA_STORE_BASE_DIRECTORY, 'monthly.p')

# Deprecating the *_FILENAME constants in favor
# of the more concise *_PATH. Retain these for now
# for backwards-compatibility
DAILY_DATA_STORE_FILENAME = DAILY_DATA_STORE_PATH
MONTHLY_DATA_STORE_FILENAME = MONTHLY_DATA_STORE_PATH
