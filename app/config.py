import logging
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, StrictInt, StrictStr, root_validator, validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("config")


class MeterConfig(BaseModel):
    id: int
    name: str
    offset: float = 0


class RoomConfig(BaseModel):
    name: StrictStr
    meters: List[MeterConfig]


class RoomsConfig(BaseModel):
    rooms: List[RoomConfig]


def get_config(configfile: Path) -> RoomsConfig:
    """
    Parse the config file into a Pydantic model.

    Parameters
    ----------
    configfile : str
        Path to the config file including file name and extension.

    Returns
    -------
    ShellyInfluxConfig
        Parsed and validated config.
    """

    if configfile.suffix not in [".yaml", ".yml"]:
        raise ValueError("Config file must be YAML with suffix .yaml or .yml")
    with open(configfile) as f:
        config = yaml.safe_load(f)
        return RoomsConfig(**config)
