"""
A bare-bones API to control Sengled smart devices via their cloud.
"""

import os

from .sengled import SengledAPI

def api(*args, **kwargs):
    return SengledAPI(*args, **kwargs)

def api_from_env():
    """
    Create an API client based on environment variables:

    * SENGLED_USERNAME
    * SENGLED_PASSWORD
    * SENGLED_SESSION_PATH (optional)
    * SENGLED_DEBUG (optional, default: False)
    """
    return api(
        username     = os.environ["SENGLED_USERNAME"],
        password     = os.environ["SENGLED_PASSWORD"],
        session_path = os.environ.get("SENGLED_SESSION_PATH"),
        debug        = os.environ.get("SENGLED_DEBUG", "false").lower() in ["true", "1", "yes", "t"],
    )
