#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Metrics Exporter for Network Monitor

Now also exports active connection details (IPs/domains).
"""

import time
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    from prometheus_client import start_http_server, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client not installed. Prometheus export will not be available.")
    PROMETHEUS_AVAILABLE = False

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    logger.warning("influxdb_client not installed. InfluxDB export will not be available.")
    INFLUXDB_AVAILABLE = False


class PrometheusExporter:
    """Export network metrics to Prometheus."""

    def __init__(self, port: int = 8000):
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client is required for Prometheus export")

        self.port = port
        self.upload_gauge = Gauge('network_upload_mbps', 'Network upload speed in Mbps')
        self.download_gauge = Gauge('network_download_mbps', 'Network download speed in Mbps')
        self.active_connections_gauge = Gauge(
            'network_active_connections', 'Number of active network connections'
        )
        self.connection_info_gauge = Gauge(
            'network_connection_info',
            'Active connection info (value=1 means active)',
            ['remote_ip', 'hostname', 'port']
        )
        self.server_started = False

    def start_server(self):
        if not self.server_started:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
            self.server_started = True

    def export_metrics(
        self,
        upload_speed: float,
        download_speed: float,
        connections: Optional[List[Dict]] = None
    ):
        if not self.server_started:
            self.start_server()

        self.upload_gauge.set(upload_speed)
        self.download_gauge.set(download_speed)

        if connections is not None:
            self.active_connections_gauge.set(len(connections))

            # Reset old values
            self.connection_info_gauge.clear()

            for conn in connections:
                self.connection_info_gauge.labels(
                    remote_ip=conn.get("remote_ip", "unknown"),
                    hostname=conn.get("hostname", "N/A"),
                    port=str(conn.get("remote_port", "0"))
                ).set(1)

        logger.debug(f"Exported to Prometheus: Upload={upload_speed:.2f}, Download={download_speed:.2f}")


class InfluxDBExporter:
    """Export network metrics to InfluxDB."""

    def __init__(self, url="http://localhost:8086", token="", org="", bucket="network_metrics",
                 batch_size=10, flush_interval=10):
        if not INFLUXDB_AVAILABLE:
            raise ImportError("influxdb_client is required for InfluxDB export")

        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.points_buffer: List[Point] = []
        self.last_flush_time = time.time()

        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"InfluxDB exporter initialized for {url}, bucket: {bucket}")

    def export_metrics(
        self,
        upload_speed: float,
        download_speed: float,
        tags: Optional[Dict[str, str]] = None,
        connections: Optional[List[Dict]] = None
    ):
        point = Point("network_bandwidth")
        if tags:
            for k, v in tags.items():
                point = point.tag(k, v)

        point = point.field("upload_mbps", upload_speed)
        point = point.field("download_mbps", download_speed)
        self.points_buffer.append(point)

        if connections:
            for conn in connections:
                conn_point = Point("network_connection") \
                    .tag("remote_ip", conn.get("remote_ip", "unknown")) \
                    .tag("hostname", conn.get("hostname", "N/A")) \
                    .tag("port", str(conn.get("remote_port", "0"))) \
                    .field("active", 1)
                if tags:
                    for k, v in tags.items():
                        conn_point = conn_point.tag(k, v)
                self.points_buffer.append(conn_point)

        current_time = time.time()
        if (len(self.points_buffer) >= self.batch_size or
                (current_time - self.last_flush_time) >= self.flush_interval):
            self.flush()

    def flush(self):
        if not self.points_buffer:
            return
        try:
            self.write_api.write(bucket=self.bucket, record=self.points_buffer)
            logger.debug(f"Flushed {len(self.points_buffer)} points to InfluxDB")
            self.points_buffer = []
            self.last_flush_time = time.time()
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    def close(self):
        self.flush()
        self.client.close()
        logger.info("InfluxDB connection closed")


class MetricsExporter:
    """Unified interface for exporting metrics to different backends."""

    def __init__(self):
        self.exporters = []

    def add_prometheus_exporter(self, port: int = 8000):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Cannot add Prometheus exporter: prometheus_client not installed")
            return False
        try:
            exporter = PrometheusExporter(port=port)
            self.exporters.append(exporter)
            logger.info(f"Prometheus exporter added on port {port}")
            return True
        except Exception as e:
            logger.error(f"Error adding Prometheus exporter: {e}")
            return False

    def add_influxdb_exporter(self, url="http://localhost:8086", token="", org="",
                              bucket="network_metrics", batch_size=10, flush_interval=10):
        if not INFLUXDB_AVAILABLE:
            logger.warning("Cannot add InfluxDB exporter: influxdb_client not installed")
            return False
        try:
            exporter = InfluxDBExporter(
                url=url, token=token, org=org, bucket=bucket,
                batch_size=batch_size, flush_interval=flush_interval
            )
            self.exporters.append(exporter)
            logger.info(f"InfluxDB exporter added for {url}, bucket: {bucket}")
            return True
        except Exception as e:
            logger.error(f"Error adding InfluxDB exporter: {e}")
            return False

    def export_metrics(
        self,
        upload_speed: float,
        download_speed: float,
        tags: Optional[Dict[str, str]] = None,
        connections: Optional[List[Dict]] = None
    ):
        for exporter in self.exporters:
            try:
                if isinstance(exporter, PrometheusExporter):
                    exporter.export_metrics(upload_speed, download_speed, connections)
                elif isinstance(exporter, InfluxDBExporter):
                    exporter.export_metrics(upload_speed, download_speed, tags, connections)
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")

    def close(self):
        for exporter in self.exporters:
            try:
                if hasattr(exporter, 'close'):
                    exporter.close()
            except Exception as e:
                logger.error(f"Error closing exporter: {e}")
