FROM python:3
ENV DATA_MINER_URI=https://s3.amazonaws.com/kcm-alerts-realtime-prod/vehiclepositions_enhanced.json
ENV TELEMETRY_SERVER_URI=http://telemetry-service
ENV PUSH_GATEWAY_URI=http://pushgateway:9091

WORKDIR /job
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY miner.py .


CMD ["python", "./miner.py"]
