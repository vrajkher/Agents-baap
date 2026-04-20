from enum import Enum


class ExecutionMode(str, Enum):
    LOCAL_FIRST = "LOCAL_FIRST"
    CLOUD_FIRST = "CLOUD_FIRST"
    HYBRID = "HYBRID"


class NetworkMode(str, Enum):
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"
    DISABLED = "DISABLED"


class PrivacyLevel(str, Enum):
    STRICT = "STRICT"
    BALANCED = "BALANCED"
    OPEN = "OPEN"
