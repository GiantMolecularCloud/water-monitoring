FROM python:3.10-slim
LABEL maintainer="@GiantMolecularCloud"

EXPOSE 8501

WORKDIR /app
COPY docker/requirements.txt .
COPY ./app /app

RUN pip config set global.no-cache-dir false
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "streamlit", "run"]
CMD ["/app/water-monitoring.py"]