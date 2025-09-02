#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Network Traffic Generator for Testing

This script generates artificial network traffic to test the Network Bandwidth Monitor.
It simulates both upload and download traffic by sending and receiving data.
"""

import time
import socket
import random
import argparse
import threading
from urllib.request import urlopen

def generate_download_traffic(duration=60, intensity=5):
    """
    Generate download traffic by downloading data from the internet.
    
    Args:
        duration (int): Duration in seconds to generate traffic
        intensity (int): Intensity level (1-10) affecting the size and frequency of downloads
    """
    print(f"Generating download traffic for {duration} seconds (intensity: {intensity})...")
    
    # List of URLs to download from (add more as needed)
    urls = [
        "https://speed.hetzner.de/100MB.bin",
        "https://proof.ovh.net/files/100Mb.dat",
        "https://speed.cloudflare.com/__down?bytes=10000000"
    ]
    
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            # Select a random URL
            url = random.choice(urls)
            
            # Download data (with a timeout to prevent hanging)
            response = urlopen(url, timeout=5)
            
            # Read data in chunks to control the download rate
            chunk_size = 1024 * intensity
            while True:
                data = response.read(chunk_size)
                if not data:
                    break
                
                # Pause briefly to control download rate
                time.sleep(0.01 / intensity)
                
        except Exception as e:
            print(f"Download error: {e}")
            time.sleep(1)
        
        # Pause between downloads
        time.sleep(max(0.1, 1 - (intensity / 10)))

def generate_upload_traffic(duration=60, intensity=5):
    """
    Generate upload traffic by sending data to a remote server.
    
    Args:
        duration (int): Duration in seconds to generate traffic
        intensity (int): Intensity level (1-10) affecting the size and frequency of uploads
    """
    print(f"Generating upload traffic for {duration} seconds (intensity: {intensity})...")
    
    # List of servers to upload to (these are echo servers that will discard the data)
    servers = [
        ("tcpbin.com", 4242),
        ("echo.websocket.org", 80),
        ("localhost", 8000)  # Fallback to localhost if external servers are unavailable
    ]
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # Try each server until one works
        for host, port in servers:
            try:
                # Create a socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((host, port))
                    
                    # Generate random data to send
                    data_size = 1024 * 1024 * intensity  # Size in bytes
                    data = b'X' * data_size
                    
                    # Send data in chunks
                    chunk_size = 1024 * intensity
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i+chunk_size]
                        s.sendall(chunk)
                        time.sleep(0.01 / intensity)  # Control upload rate
                    
                    break  # If successful, break the server loop
            except Exception as e:
                print(f"Upload error ({host}:{port}): {e}")
                continue
        
        # Pause between uploads
        time.sleep(max(0.1, 1 - (intensity / 10)))

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Network Traffic Generator for Testing')
    
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration in seconds to generate traffic (default: 60)')
    parser.add_argument('--download-intensity', type=int, default=5,
                        help='Download intensity level 1-10 (default: 5)')
    parser.add_argument('--upload-intensity', type=int, default=5,
                        help='Upload intensity level 1-10 (default: 5)')
    parser.add_argument('--download-only', action='store_true',
                        help='Generate only download traffic')
    parser.add_argument('--upload-only', action='store_true',
                        help='Generate only upload traffic')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    # Validate intensity levels
    args.download_intensity = max(1, min(10, args.download_intensity))
    args.upload_intensity = max(1, min(10, args.upload_intensity))
    
    # Determine which traffic types to generate
    generate_download = not args.upload_only
    generate_upload = not args.download_only
    
    # Create threads for traffic generation
    threads = []
    
    if generate_download:
        download_thread = threading.Thread(
            target=generate_download_traffic,
            args=(args.duration, args.download_intensity)
        )
        threads.append(download_thread)
    
    if generate_upload:
        upload_thread = threading.Thread(
            target=generate_upload_traffic,
            args=(args.duration, args.upload_intensity)
        )
        threads.append(upload_thread)
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for threads to complete
    for thread in threads:
        thread.join()
    
    print("Traffic generation completed.")