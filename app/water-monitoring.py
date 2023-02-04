"""Water monitoring

A little streamlit frontend to log manual water meter readings to a InfluxDB backend.

Author: GiantMolecularCloud
Version: 0.2
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import influxdb.exceptions as inexc
import streamlit as st
from influxdb import InfluxDBClient
from pytz import timezone

from config import RoomsConfig, get_config


####################################################################################################
# SETUP
####################################################################################################

config = get_config(Path("config/config.yaml"))

logging.basicConfig(level=logging.INFO)

st.set_page_config(initial_sidebar_state='expanded',
                   layout='wide'
                   )

# set up database connection and select the right database

# get influxdb settings from environment variables
INFLUX_IP = os.getenv('INFLUX_IP') or '127.0.0.1'
INFLUX_PORT = int(os.getenv('INFLUX_PORT') or 8086)
INFLUX_USER = os.getenv('INFLUX_USER') or 'root'
INFLUX_PASSWD = os.getenv('INFLUX_PASSWD') or 'root'
DB_NAME = os.getenv('DB_NAME') or 'water-monitoring'
TIMEZONE = os.getenv('TIMEZONE') or 'Europe/Berlin'
DEBUG = bool(os.getenv('DEBUG')) or False

# connect to influxdb database
client = InfluxDBClient(host=INFLUX_IP,
                        port=INFLUX_PORT,
                        username=INFLUX_USER,
                        password=INFLUX_PASSWD
                        )

# create new database if necessary
if not DB_NAME in [db['name'] for db in client.get_list_database()]:
    client.create_database(DB_NAME)

# select current database
client.switch_database(DB_NAME)


def query_last(
    client: InfluxDBClient,
    room_name: str,
    meter_name: str,
) -> float:

    try:
        iresponse = client.query(
            f"SELECT last(\"{meter_name}\") FROM \"{room_name}\""
        ).get_points()
        if not iresponse:
            raise ConnectionError(
                "Sending data to database failed.", iresponse)
        return list(iresponse)[0]['last']
    except ConnectionError as e:
        logging.error("Connection Error.\n", e)
    except inexc.InfluxDBServerError as e:
        logging.error("Querying latest readings from database failed due to timeout.\n", e)
    except Exception as e:
        logging.error("Encountered unknown error.\n", e)


def get_latest_readings(
    client: InfluxDBClient,
    rooms: RoomsConfig,
) -> Dict[str, Dict[str, float]]:
    """
    Get the latest water meter readings from the database.

    Parameters
    ----------
    client : InfluxDBClient
        The InfluxDB client to write the data to.

    Raises
    ------
    ConnectionError
        Raised if the client cannot be reached.
    """

    return {
        room.name: {meter.name: query_last(client, room.name, meter.name)-meter.offset for meter in room.meters} for room in rooms
    }


class WaterReading:
    """
    Wrapper class to format and handle the data.
    This will be extended more functionality later.
    """

    def __init__(
        self,
        date: datetime.date,
        time: datetime.time,
        room_name: str,
        readings: dict,
    ) -> None:
        """
        Format data in an InfluxDB compatible dictionary.
        The various groups of detailed information are separated using tags as field names can occur multiple times.
        InfluxDB stores timestamps in UTC, so it is up to the user to take care of timezones.
        """
        isodate = datetime.combine(date, time)
        isodate = isodate.astimezone(timezone(TIMEZONE))
        for meter_name, value in readings.items():
            if value == 0.0:
                readings[meter_name] = None
        self.data = [{'measurement': room_name,
                      'time': isodate,
                      'fields': readings
                      }]

    def display(self) -> None:
        """
        Display the data in streamlit.
        """
        st.info(f"Data logged.")
        if DEBUG:
            st.write('Saved values:')
            st.write(self.data)

    def write_to_database(self, client: InfluxDBClient) -> None:
        """
        Write the data to the database.

        Parameters
        ----------
        client : InfluxDBClient
            The InfluxDB client to write the data to.

        Raises
        ------
        ConnectionError
            Raised if the client cannot be reached.
        """
        try:
            logging.debug(f"Writing points: {self.data}")
            iresponse = client.write_points(self.data)
            logging.debug(f"InfuxDB response: {iresponse}")
            if not iresponse:
                raise ConnectionError(
                    "Sending data to database failed.", iresponse)
            self.display()
        except ConnectionError as e:
            logging.error("Connection Error.\n", e)
        except inexc.InfluxDBServerError as e:
            logging.error("Sending data to database failed due to timeout.\n", e)
        except Exception as e:
            logging.error("Encountered unknown error.\n", e)


####################################################################################################
# SIDEBAR
####################################################################################################

# None


####################################################################################################
# MAIN
####################################################################################################

st.markdown("""
    <style>
        .appview-container .main .block-container{padding-top: 1rem; padding-bottom: 1rem;}
    </style>""",
            unsafe_allow_html=True,
            )
st.title('Water Monitoring')


# data entry
####################################################################################################

latest_readings = get_latest_readings(client, config.rooms)

st.write('Enter water meter readings:')

# get inputs
col1, col2 = st.columns(2)
with col1:
    date = st.date_input(label='Date',
                         help='Date on which the water meter was read.'
                         )
with col2:
    time = st.time_input(label='Time',
                         help='Time at which the water meter was read.'
                         )
st.text("")

for room in config.rooms:

    cols = st.columns(len(room.meters)+1)
    with cols[0]:
        st.header(room.name)
    
    readings = {}
    for col,meter in zip(cols[1:],room.meters):
        with col:
            value = latest_readings[room.name][meter.name]
            st.metric(
                label=f"{room.name} {meter.name}",
                value=value,
                delta=value-latest_readings[room.name][meter.name]
            )
            value = st.number_input(
                label='new value:',
                value=value,
                step=0.001,
                format='%.3f',
                key=f'{room.name}_{meter.name}'
            )
            readings[meter.name] = value + meter.offset

    st.text("")
    if st.button(label='Send', key=f"send_{room.name}"):
        data = WaterReading(date, time, room.name, readings)
        data.write_to_database(client)
