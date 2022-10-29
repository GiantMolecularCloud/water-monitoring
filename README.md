# Water Monitoring

A simple streamlit frontend to log water meter readings into InfluxDB.

Two rooms with two water meters each are implemented and labelled 'kitchen' and 'bathroom'.
To add more roomes, just append to the rooms list (`ROOMS`) in the setup section.

## Local execution

Install streamlit and influxdb:  
`pip install -r docker/requirements.txt`

Run the app in Streamlit:  
`streamlit run app/water-monitoring.py`

## docker

Build the image:  
`docker build -t water-monitoring:0.1 -f docker/Dockerfile .`

Run the container:  
`docker run -p 8501:8501 water-monitoring:0.1 water-monitoring`

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

## Example Dashboard

A very simple dashboard to show the entered values could look like this in Grafana:

![example dashboard](docs/dashboard.png?raw=true "Example dashboard")
