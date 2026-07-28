# Alpine plus bind-tools, because the collector reads the live _ts3._udp SRV
# record on every cycle and dig is the smallest reliable way to do that.
FROM python:3.13-alpine

RUN apk add --no-cache bind-tools

COPY collector.py /usr/local/bin/collector.py
RUN chmod 0755 /usr/local/bin/collector.py

# Writes /textfile/teamspeak.prom, which the host's node_exporter picks up.
ENTRYPOINT ["python3", "-u", "/usr/local/bin/collector.py"]
