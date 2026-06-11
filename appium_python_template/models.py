import json
import time
from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional

class NavigationType(Enum):
    APPIUM = "appium"
    JSNAV = "jsnav"
    XCTEST = "xctest"
    GUIDED = "guided"


class ErrorCodes(Enum):
    FAILED_TO_LAUNCH = "FAILED_TO_LAUNCH_CA"
    WORKFLOW_ERROR = "WORKFLOW_ERROR_CA"
    BAD_CREDS = "BAD_CREDS_CA"
    POST_LOGIN_WORKFLOW_ERROR = "POST_LOGIN_WORKFLOW_ERROR_CA"
    LOGIN_UNKNOWN = "LOGIN_UNKNOWN_CA"
    SUBMISSION_FAILURE = "SUBMISSION_FAILURE_CA"


@dataclass
class RunData:
    navigation_type: NavigationType
    login_success: bool = False
    data_written: str = "{{mm.dd.yyyy}}"  # <- Update with last modified date!
    rundata_version: str = "3.0"
    error_code: Optional[ErrorCodes] = ErrorCodes.FAILED_TO_LAUNCH

    def to_dict(self):
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            # Uses values for Enums
            if hasattr(value, "value"):
                result[f.name] = value.value
            else:
                result[f.name] = value
        return result

    def dumps(self):
        return json.dumps(self.to_dict())


def generate_schema():
    """
    Used to generate a JSON schema for the python built-in dataclass.
    """
    from pydantic import TypeAdapter
    schema = TypeAdapter(RunData).json_schema()
    return json.dumps(schema, indent=2)


run_data = RunData(navigation_type=NavigationType.APPIUM)
