#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Network Bandwidth Monitor

This script monitors network bandwidth usage, detects consumption spikes,
and triggers alerts when certain thresholds are exceeded.
"""

import time
import psutil
import logging
import argparse
from datetime import datetime
import socket

try:
    from metrics_exporter import MetricsExporter
    METRICS_EXPORT_AVAILABLE = True
except ImportError:
    METRICS_EXPORT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("network_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default thresholds in Mbps
DEFAULT_THRESHOLDS = {
    'upload': 100,  # 50 Mbps
    'download': 150  # 100 Mbps
}


def get_active_connections(limit=5):
    """
    Get active network connections (basic info: remote IP, port, hostname).

    Args:
        limit (int): Maximum number of connections to return
    Returns:
        list of dict: Connection details
    """
    conns = psutil.net_connections(kind="inet")
    results = []
    for c in conns:
        if c.raddr:  # só conexões remotas
            ip = c.raddr.ip
            try:
                host = socket.gethostbyaddr(ip)[0]
            except Exception:
                host = None
            results.append({
                "remote_ip": ip,
                "remote_port": c.raddr.port,
                "hostname": host or "N/A"
            })
    return results[:limit]


class NetworkMonitor:
    """Monitor network bandwidth and trigger alerts on threshold violations."""

    def __init__(self, thresholds=None, interval=1, metrics_exporter=None):
        """
        Initialize the network monitor.

        Args:
            thresholds (dict): Dictionary with 'upload' and 'download' thresholds in Mbps
            interval (float): Monitoring interval in seconds
            metrics_exporter (MetricsExporter, optional): Exporter for metrics to time-series databases
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.interval = interval
        self.prev_net_io = None
        self.metrics_exporter = metrics_exporter
        logger.info(f"Network monitor initialized with thresholds: {self.thresholds}")

    def get_network_usage(self):
        """Get current network usage statistics."""
        return psutil.net_io_counters()

    def calculate_bandwidth(self, current_net_io):
        """
        Calculate bandwidth usage based on previous and current measurements.

        Returns:
            tuple: (upload_speed_mbps, download_speed_mbps)
        """
        if self.prev_net_io is None:
            self.prev_net_io = current_net_io
            return 0, 0

        # Calculate bytes transferred during the interval
        bytes_sent = current_net_io.bytes_sent - self.prev_net_io.bytes_sent
        bytes_recv = current_net_io.bytes_recv - self.prev_net_io.bytes_recv

        # Convert to Mbps (Megabits per second)
        upload_speed_mbps = (bytes_sent * 8) / (self.interval * 1_000_000)
        download_speed_mbps = (bytes_recv * 8) / (self.interval * 1_000_000)

        # Update previous values
        self.prev_net_io = current_net_io

        return upload_speed_mbps, download_speed_mbps

    def check_thresholds(self, upload_speed, download_speed):
        """
        Check if network usage exceeds defined thresholds.

        Args:
            upload_speed (float): Upload speed in Mbps
            download_speed (float): Download speed in Mbps
        """
        if upload_speed > self.thresholds['upload']:
            logger.warning(f"ALERT: Upload threshold exceeded! Current: {upload_speed:.2f} Mbps, Threshold: {self.thresholds['upload']} Mbps")
            self.trigger_alert("upload", upload_speed, self.thresholds['upload'])

        if download_speed > self.thresholds['download']:
            logger.warning(f"ALERT: Download threshold exceeded! Current: {download_speed:.2f} Mbps, Threshold: {self.thresholds['download']} Mbps")
            self.trigger_alert("download", download_speed, self.thresholds['download'])

    def trigger_alert(self, direction, current_value, threshold):
        """
        Trigger an alert when a threshold is exceeded.

        Args:
            direction (str): 'upload' or 'download'
            current_value (float): Current bandwidth usage in Mbps
            threshold (float): Threshold value in Mbps
        """
        # This is a placeholder for alert implementation
        # In a real-world scenario, this could send emails, SMS, or integrate with monitoring systems
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_message = f"[{timestamp}] {direction.upper()} ALERT: {current_value:.2f} Mbps exceeds threshold of {threshold} Mbps"

        # Log the alert (already done in check_thresholds, but keeping for demonstration)
        logger.warning(alert_message)

        # Here you could add code to send the alert via other channels
        # For example: send_email(), send_sms(), post_to_slack(), etc.

    def monitor(self, duration=None):
        """
        Start monitoring network bandwidth.

        Args:
            duration (int, optional): Duration to monitor in seconds. If None, runs indefinitely.
        """
        global active_conns
        logger.info("Starting network monitoring...")
        start_time = time.time()

        try:
            while True:
                # Check if monitoring duration has elapsed
                if duration and (time.time() - start_time) > duration:
                    logger.info(f"Monitoring completed after {duration} seconds")
                    break

                # Get current network usage
                current_net_io = self.get_network_usage()

                # Calculate bandwidth
                upload_speed, download_speed = self.calculate_bandwidth(current_net_io)

                # Log current bandwidth usage
                if upload_speed > 0 or download_speed > 0:  # Only log if there's actual traffic
                    logger.info(f"Upload: {upload_speed:.2f} Mbps, Download: {download_speed:.2f} Mbps")
                    # 🔎 também loga conexões ativas
                    active_conns = get_active_connections(limit=5)
                    for conn in active_conns:
                        logger.info(
                            f"Conn -> {conn['remote_ip']}:{conn['remote_port']} ({conn['hostname']})"
                        )

                # Export metrics if exporter is available
                if self.metrics_exporter:
                    try:
                        # Get network interfaces
                        net_if_addrs = psutil.net_if_addrs()

                        # Initialize variables with default values
                        host_addr = "unknown"
                        interface_name = "unknown"

                        # Get the first interface name (usually the main one)
                        if net_if_addrs:
                            try:
                                interface_name = list(net_if_addrs.keys())[0]
                                # Get the first address object for this interface
                                if net_if_addrs[interface_name] and len(net_if_addrs[interface_name]) > 0:
                                    addr_info = net_if_addrs[interface_name][0]
                                    # Check if it's a proper address object or a dict
                                    if hasattr(addr_info, 'address'):
                                        host_addr = addr_info.address
                                    elif isinstance(addr_info, dict) and 'address' in addr_info:
                                        host_addr = addr_info['address']
                            except (IndexError, KeyError, AttributeError) as e:
                                logger.debug(f"Error getting network interface details: {e}")

                           ##self.metrics_exporter.export_metrics(upload_speed=float(upload_speed),download_speed=float(download_speed),tags={"host": host_addr, "interface": interface_name},connections=active_conns)

                    except Exception as e:
                        logger.error(f"Error exporting metrics: {e}")

                # Check if thresholds are exceeded
                self.check_thresholds(upload_speed, download_speed)

                # Wait for the next interval
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Network Bandwidth Monitor')

    # Monitoring configuration
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Monitoring interval in seconds (default: 1.0)')
    parser.add_argument('--duration', type=int, default=None,
                        help='Duration to monitor in seconds (default: indefinitely)')

    # Threshold configuration
    parser.add_argument('--upload-threshold', type=float, default=50.0,
                        help='Upload threshold in Mbps (default: 50.0)')
    parser.add_argument('--download-threshold', type=float, default=100.0,
                        help='Download threshold in Mbps (default: 100.0)')

    # Prometheus configuration
    parser.add_argument('--prometheus', action='store_true',
                        help='Enable Prometheus metrics export')
    parser.add_argument('--prometheus-port', type=int, default=8000,
                        help='Port for Prometheus metrics server (default: 8000)')

    # InfluxDB configuration
    parser.add_argument('--influxdb', action='store_true',
                        help='Enable InfluxDB metrics export')
    parser.add_argument('--influxdb-url', type=str, default='http://localhost:8086',
                        help='InfluxDB server URL (default: http://localhost:8086)')
    parser.add_argument('--influxdb-token', type=str, default='',
                        help='InfluxDB API token')
    parser.add_argument('--influxdb-org', type=str, default='',
                        help='InfluxDB organization')
    parser.add_argument('--influxdb-bucket', type=str, default='network_metrics',
                        help='InfluxDB bucket (default: network_metrics)')

    return parser.parse_args()


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Configure thresholds
    custom_thresholds = {
        'upload': args.upload_threshold,
        'download': args.download_threshold
    }

    # Configure metrics exporter if enabled
    metrics_exporter = None
    if METRICS_EXPORT_AVAILABLE and (args.prometheus or args.influxdb):
        metrics_exporter = MetricsExporter()

        # Add Prometheus exporter if enabled
        if args.prometheus:
            success = metrics_exporter.add_prometheus_exporter(port=args.prometheus_port)
            if not success:
                logger.warning("Failed to add Prometheus exporter. Continuing without Prometheus.")

        # Add InfluxDB exporter if enabled
        if args.influxdb:
            success = metrics_exporter.add_influxdb_exporter(
                url=args.influxdb_url,
                token=args.influxdb_token,
                org=args.influxdb_org,
                bucket=args.influxdb_bucket
            )
            if not success:
                logger.warning("Failed to add InfluxDB exporter. Continuing without InfluxDB.")

    try:
        # Create and start the monitor
        monitor = NetworkMonitor(
            thresholds=custom_thresholds,
            interval=args.interval,
            metrics_exporter=metrics_exporter
        )

        # Start monitoring
        monitor.monitor(duration=args.duration)
    finally:
        # Ensure metrics exporter is properly closed
        if metrics_exporter:
            try:
                metrics_exporter.close()
            except Exception as e:
                logger.error(f"Error closing metrics exporter: {e}")
