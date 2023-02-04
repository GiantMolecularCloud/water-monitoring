# Water Monitoring

A simple streamlit frontend to log water meter readings into InfluxDB.

Two rooms with two water meters each are implemented and labelled 'kitchen' and 'bathroom'.
To add more roomes, just append to the rooms list (`ROOMS`) in the setup section.

## Local execution

Install streamlit and influxdb:  
`pip install -r docker/requirements.txt`

Run the app in Streamlit from within the app directory:
`streamlit run water-monitoring.py`

## docker

Build the image:  
`docker build -t water-monitoring:latest -f docker/Dockerfile .`

Run the container:  
`docker run -p 8501:8501 -v /path/to/your/config/directory:/config water-monitoring:latest water-monitoring`

## Options

If InfluxDB does not run with default values, the connection details can be set through env variables. Further options are also available.
When no variables are given, the following defaults are assumed:

| env variable  | default            |
| ------------- | ------------------ |
| INFLUX_IP     | '127.0.0.1'        |
| INFLUX_PORT   | 8086               |
| INFLUX_USER   | 'root'             |
| INFLUX_PASSWD | 'root'             |
| DB_NAME       | 'water-monitoring' |
| TIMEZONE      | 'Europe/Berlin'    |
| DEBUG         | False              |

## Water meter configuration

The water meters are configured in a yaml config file, see `config/config.yaml` for an example.
An umlimited number of rooms with each an unlimited number of water meters is supported.
The structure is as follows:

-   rooms: list of rooms
-   each room must be given a name and a list of water meters
-   each water meter has an ID, name and offset. The offset is added to the actual meter readings to get coherent measurements when the meter is replaced.

The app expects the config file to be located in `config/config.yaml`. When run in docker, your config must therefore be passed through with a `volume` argument.

## Frontend

This is how the Streamlit app looks like when opened in a browser:

![app frontend](docs/frontend.png?raw=true "App frontend")

## Example Dashboard

A very simple dashboard to show the entered values could look like this in Grafana:

![example dashboard](docs/dashboard.png?raw=true "Example dashboard")
