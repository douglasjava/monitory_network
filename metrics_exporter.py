#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Metrics Exporter for Network Monitor

This module provides functionality to export network metrics to time-series databases
like Prometheus (via a metrics endpoint) or InfluxDB (via direct writes).
"""

import time
import logging
from datetime import datetime
from typing import Dict, Optional, Union, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

try:
    # Optional dependencies - may not be installed
    from prometheus_client import start_http_server, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client not installed. Prometheus export will not be available.")
    PROMETHEUS_AVAILABLE = False

try:
    # Optional dependencies - may not be installed
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    logger.warning("influxdb_client not installed. InfluxDB export will not be available.")
    INFLUXDB_AVAILABLE = False


class PrometheusExporter:
    """Export network metrics to Prometheus."""
    
    def __init__(self, port: int = 8000):
        """
        Initialize the Prometheus exporter.
        
        Args:
            port (int): Port to expose Prometheus metrics on
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client is required for Prometheus export")
        
        self.port = port
        self.upload_gauge = Gauge('network_upload_mbps', 'Network upload speed in Mbps')
        self.download_gauge = Gauge('network_download_mbps', 'Network download speed in Mbps')
        self.server_started = False
        
    def start_server(self):
        """Start the Prometheus metrics server."""
        if not self.server_started:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
            self.server_started = True
        
    def export_metrics(self, upload_speed: float, download_speed: float):
        """
        Export network metrics to Prometheus.
        
        Args:
            upload_speed (float): Upload speed in Mbps
            download_speed (float): Download speed in Mbps
        """
        if not self.server_started:
            self.start_server()
            
        self.upload_gauge.set(upload_speed)
        self.download_gauge.set(download_speed)
        logger.debug(f"Metrics exported to Prometheus: Upload={upload_speed:.2f} Mbps, Download={download_speed:.2f} Mbps")


class InfluxDBExporter:
    """Export network metrics to InfluxDB."""
    
    def __init__(
        self, 
        url: str = "http://localhost:8086", 
        token: str = "", 
        org: str = "", 
        bucket: str = "network_metrics",
        batch_size: int = 10,
        flush_interval: int = 10
    ):
        """
        Initialize the InfluxDB exporter.
        
        Args:
            url (str): InfluxDB server URL
            token (str): InfluxDB API token
            org (str): InfluxDB organization
            bucket (str): InfluxDB bucket to write to
            batch_size (int): Number of points to batch before writing
            flush_interval (int): Maximum seconds to wait before flushing batch
        """
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
        
        # Initialize InfluxDB client
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"InfluxDB exporter initialized for {url}, bucket: {bucket}")
        
    def export_metrics(
        self, 
        upload_speed: float, 
        download_speed: float, 
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Export network metrics to InfluxDB.
        
        Args:
            upload_speed (float): Upload speed in Mbps
            download_speed (float): Download speed in Mbps
            tags (dict, optional): Additional tags to add to the data point
        """
        # Create a data point
        point = Point("network_bandwidth")
        
        # Add tags
        if tags:
            for key, value in tags.items():
                point = point.tag(key, value)
        
        # Add fields
        point = point.field("upload_mbps", upload_speed)
        point = point.field("download_mbps", download_speed)
        
        # Add to buffer
        self.points_buffer.append(point)
        
        # Check if we should flush the buffer
        current_time = time.time()
        if (len(self.points_buffer) >= self.batch_size or 
            (current_time - self.last_flush_time) >= self.flush_interval):
            self.flush()
    
    def flush(self):
        """Flush buffered points to InfluxDB."""
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
        """Close the InfluxDB client connection."""
        self.flush()  # Ensure any remaining points are written
        self.client.close()
        logger.info("InfluxDB connection closed")


class MetricsExporter:
    """
    Unified interface for exporting metrics to different backends.
    
    This class provides a single interface to export metrics to multiple
    backends simultaneously (Prometheus, InfluxDB, etc.).
    """
    
    def __init__(self):
        """Initialize the metrics exporter."""
        self.exporters = []
        
    def add_prometheus_exporter(self, port: int = 8000):
        """
        Add a Prometheus exporter.
        
        Args:
            port (int): Port to expose Prometheus metrics on
        
        Returns:
            bool: True if exporter was added successfully, False otherwise
        """
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
    
    def add_influxdb_exporter(
        self, 
        url: str = "http://localhost:8086", 
        token: str = "", 
        org: str = "", 
        bucket: str = "network_metrics",
        batch_size: int = 10,
        flush_interval: int = 10
    ):
        """
        Add an InfluxDB exporter.
        
        Args:
            url (str): InfluxDB server URL
            token (str): InfluxDB API token
            org (str): InfluxDB organization
            bucket (str): InfluxDB bucket to write to
            batch_size (int): Number of points to batch before writing
            flush_interval (int): Maximum seconds to wait before flushing batch
        
        Returns:
            bool: True if exporter was added successfully, False otherwise
        """
        if not INFLUXDB_AVAILABLE:
            logger.warning("Cannot add InfluxDB exporter: influxdb_client not installed")
            return False
            
        try:
            exporter = InfluxDBExporter(
                url=url, 
                token=token, 
                org=org, 
                bucket=bucket,
                batch_size=batch_size,
                flush_interval=flush_interval
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
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Export metrics to all configured exporters.
        
        Args:
            upload_speed (float): Upload speed in Mbps
            download_speed (float): Download speed in Mbps
            tags (dict, optional): Additional tags to add to the data points
        """
        for exporter in self.exporters:
            try:
                if isinstance(exporter, PrometheusExporter):
                    exporter.export_metrics(upload_speed, download_speed)
                elif isinstance(exporter, InfluxDBExporter):
                    exporter.export_metrics(upload_speed, download_speed, tags)
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")
    
    def close(self):
        """Close all exporters."""
        for exporter in self.exporters:
            try:
                if hasattr(exporter, 'close'):
                    exporter.close()
            except Exception as e:
                logger.error(f"Error closing exporter: {e}")