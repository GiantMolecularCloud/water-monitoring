"""Water monitoring

A little streamlit frontend to log manual water meter readings to a InfluxDB backend.

Author: GiantMolecularCloud
Version: 0.2
"""

import os
from datetime import datetime
from typing import Dict, Literal, Optional
from pytz import timezone
import logging
import streamlit as st
from influxdb import InfluxDBClient
import influxdb.exceptions as inexc


####################################################################################################
# SETUP
####################################################################################################

ROOMS = ['bathroom', 'kitchen']

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
    room: str,
    temperature: Literal['hot', 'cold']
) -> float:

    try:
        iresponse = client.query(
            f"SELECT last(\"{temperature}\") FROM \"{room}\""
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
    client: InfluxDBClient
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
        room: {temp: query_last(client, room, temp) for temp in ['hot', 'cold']} for room in ['bathroom', 'kitchen']
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
        room: Literal['kitchen', 'bathroom'],
        hot: Optional[float] = None,
        cold: Optional[float] = None
    ) -> None:
        """
        Format data in an InfluxDB compatible dictionary.
        The various groups of detailed information are separated using tags as field names can occur multiple times.
        InfluxDB stores time stamps in UTC, so it is up to the user to take care of timezones.
        """
        isodate = datetime.combine(date, time)
        isodate = isodate.astimezone(timezone(TIMEZONE))
        if hot == 0.0:
            hot = None
        if cold == 0.0:
            cold = None
        self.data = [{'measurement': room,
                      'time': isodate,
                      'fields': {"hot": hot, "cold": cold}
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

latest_readings = get_latest_readings(client)

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

for room in ROOMS:

    col1, col2, col3 = st.columns(3)
    with col1:
        st.header(room)
    with col2:
        hot = latest_readings[room]['hot']
        st.metric(
            label=f"{room} hot",
            value=hot,
            delta=hot-latest_readings[room]['hot']
        )
        hot = st.number_input(
            label='new value:',
            value=hot,
            step=0.001,
            format='%.3f',
            key=f'{room}_hot'
        )
    with col3:
        cold = latest_readings[room]['cold']
        st.metric(
            label=f"{room} cold",
            value=cold,
            delta=cold-latest_readings[room]['cold']
        )
        cold = st.number_input(
            label='new value:',
            value=cold,
            step=0.001,
            format='%.3f',
            key=f'{room}_cold'
        )
    st.text("")
    if st.button(label='Send', key=f"send_{room}"):
        data = WaterReading(date, time, room, hot, cold)
        data.write_to_database(client)
