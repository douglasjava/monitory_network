# Network Bandwidth Monitor

A Python application that monitors network bandwidth usage, detects consumption spikes, and triggers alerts when certain thresholds are exceeded.

## Features

- Real-time monitoring of network upload and download speeds
- Configurable thresholds for triggering alerts
- Detailed logging of network activity
- Optional integration with Prometheus and InfluxDB for metrics storage and visualization

## Requirements

- Python 3.6+
- psutil library (required)
- prometheus_client library (optional, for Prometheus integration)
- influxdb_client library (optional, for InfluxDB integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/network-bandwidth-monitor.git
   cd network-bandwidth-monitor
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Linux/Mac
   ```

3. Install the dependencies:

   For just the required dependencies:
   ```
   pip install psutil
   ```

   Or, install all dependencies (including optional ones) using the requirements.txt file:
   ```
   pip install -r requirements.txt
   ```

   Or, install optional dependencies individually:
   ```
   pip install prometheus_client  # For Prometheus integration
   pip install influxdb-client    # For InfluxDB integration
   ```

## Usage

### Basic Usage

Run the monitor with default settings:

```
python network_monitor.py
```

This will monitor network bandwidth with default thresholds (50 Mbps for upload, 100 Mbps for download) and log alerts when thresholds are exceeded.

### Configuration Options

The application supports various command-line arguments for customization:

#### Monitoring Configuration

- `--interval SECONDS`: Set the monitoring interval in seconds (default: 1.0)
- `--duration SECONDS`: Set the monitoring duration in seconds (default: indefinitely)

#### Threshold Configuration

- `--upload-threshold MBPS`: Set the upload threshold in Mbps (default: 50.0)
- `--download-threshold MBPS`: Set the download threshold in Mbps (default: 100.0)

#### Prometheus Integration

- `--prometheus`: Enable Prometheus metrics export
- `--prometheus-port PORT`: Set the port for Prometheus metrics server (default: 8000)

#### InfluxDB Integration

- `--influxdb`: Enable InfluxDB metrics export
- `--influxdb-url URL`: Set the InfluxDB server URL (default: http://localhost:8086)
- `--influxdb-token TOKEN`: Set the InfluxDB API token
- `--influxdb-org ORG`: Set the InfluxDB organization
- `--influxdb-bucket BUCKET`: Set the InfluxDB bucket (default: network_metrics)

### Examples

Monitor with custom thresholds:
```
python network_monitor.py --upload-threshold 20 --download-threshold 50
```

Monitor for a specific duration:
```
python network_monitor.py --duration 3600  # Monitor for 1 hour
```

Export metrics to Prometheus:
```
python network_monitor.py --prometheus --prometheus-port 9090
```

Export metrics to InfluxDB:
```
python network_monitor.py --influxdb --influxdb-token YOUR_TOKEN --influxdb-org YOUR_ORG
```

## Visualization with Grafana

If you're using Prometheus or InfluxDB for metrics storage, you can visualize the network bandwidth metrics using Grafana:

1. Install and configure Grafana
2. Add your Prometheus or InfluxDB as a data source
3. Create a dashboard with panels for upload and download speeds

Example Grafana queries:

### Prometheus

```
rate(network_upload_mbps[5m])
rate(network_download_mbps[5m])
```

### InfluxDB (Flux query)

```
from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "network_bandwidth")
  |> filter(fn: (r) => r._field == "upload_mbps" or r._field == "download_mbps")
```

## Extending the Application

### Custom Alert Mechanisms

You can extend the `trigger_alert` method in the `NetworkMonitor` class to implement custom alert mechanisms, such as:

- Email notifications
- SMS alerts
- Integration with messaging platforms (Slack, Discord, etc.)
- Integration with monitoring systems (Nagios, Zabbix, etc.)

### Additional Metrics

You can extend the application to collect and monitor additional network metrics, such as:

- Packet loss
- Latency
- Connection count
- Per-interface bandwidth usage

## Docker Setup

This project includes a complete Docker setup for local testing and development, which includes:

- The Network Monitor application
- Prometheus for metrics collection
- InfluxDB for metrics storage
- Grafana for visualization

### Prerequisites

- Docker and Docker Compose installed on your system

### Running with Docker

1. Build and start all services:
   ```
   docker-compose up -d
   ```

2. Access the services:
   - Grafana: http://localhost:3000 (username: admin, password: admin)
   - Prometheus: http://localhost:9090
   - InfluxDB: http://localhost:8086 (username: admin, password: adminpassword)

3. Stop all services:
   ```
   docker-compose down
   ```

### Docker Architecture

The Docker setup consists of the following services:

1. **network-monitor**: The main application that monitors network bandwidth and exports metrics.
2. **prometheus**: Collects and stores metrics from the network-monitor service.
3. **influxdb**: Alternative time-series database for storing metrics.
4. **grafana**: Visualization tool for displaying metrics from Prometheus and InfluxDB.

The services are connected through a Docker network called `monitoring-network`, allowing them to communicate with each other.

### Persistent Data

The Docker setup uses volumes to persist data:

- `prometheus_data`: Stores Prometheus time-series data
- `influxdb_data`: Stores InfluxDB time-series data
- `grafana_data`: Stores Grafana dashboards, users, and other settings

This ensures that your data is preserved even if the containers are stopped or removed.

### Testing with Simulated Network Traffic

The repository includes a test script (`test_network_traffic.py`) that generates artificial network traffic to test the monitoring system. This is useful for verifying that the setup is working correctly.

To use the test script:

```
python test_network_traffic.py --duration 120 --download-intensity 7 --upload-intensity 5
```

Options:
- `--duration`: Duration in seconds to generate traffic (default: 60)
- `--download-intensity`: Download intensity level 1-10 (default: 5)
- `--upload-intensity`: Upload intensity level 1-10 (default: 5)
- `--download-only`: Generate only download traffic
- `--upload-only`: Generate only upload traffic

While the test script is running, you should see the network metrics in Grafana showing the simulated traffic.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
