#!/usr/bin/env python3
# main_remote.py
# Remote scanning through SSH tunnel

from planner import plan_with_claude
from executor import execute_commands
from parser import convert_xml_to_json
from analyzer import analyze_results
from port_extractor import extract_ports_from_json, generate_service_command
from ssh_tunnel import SSHTunnel, create_proxychains_config, test_tunnel
import json
import os
import re
import threading
from datetime import datetime


def validate_subnet(subnet):
    """Validates CIDR subnet format"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
    if not re.match(pattern, subnet):
        return False

    # Validate IP ranges
    parts = subnet.split('/')[0].split('.')
    if not all(0 <= int(p) <= 255 for p in parts):
        return False

    # Validate CIDR
    cidr = int(subnet.split('/')[1])
    if not 0 <= cidr <= 32:
        return False

    return True


# ========================================
# CONFIGURATION
# ========================================

# SSH Tunnel Configuration
SSH_HOST = "your.ssh.server.com"  # SSH server IP/hostname
SSH_USER = "username"              # SSH username
SSH_PORT = 22                      # SSH port
SSH_KEY = None                     # Path to SSH key (optional, e.g., "/home/user/.ssh/id_rsa")
SOCKS_PORT = 1080                  # Local SOCKS proxy port

# Target subnets (remote networks accessible from SSH server)
SUBNETS = [
    "10.0.0.0/24",      # Internal network 1
    "172.16.0.0/24",    # Internal network 2
    "192.168.1.0/24"    # Internal network 3
]

# ========================================

BASE_DIR = "output_remote"
os.makedirs(BASE_DIR, exist_ok=True)

print_lock = threading.Lock()


def scan_subnet(subnet, use_proxy=False, proxychains_config=None):
    """
    Function that executes a complete subnet scan
    Runs in a separate thread for parallel processing
    """
    thread_id = threading.current_thread().name

    with print_lock:
        print(f"\n[{thread_id}] Starting scan of {subnet}")
        if use_proxy:
            print(f"[{thread_id}] Using SOCKS proxy for scanning")

    start_time = datetime.now()
    try:
        # Validate subnet
        if not validate_subnet(subnet):
            with print_lock:
                print(f"[{thread_id}] [!] Invalid subnet: {subnet}")
            return

        folder_name = subnet.replace('/', '_')
        subdir = os.path.join(BASE_DIR, folder_name)
        os.makedirs(subdir, exist_ok=True)

        # Plan scan with Claude
        plan = plan_with_claude(subnet)
        commands = plan.get("commands", [])

        if not commands:
            with print_lock:
                print(f"[{thread_id}] [!] No commands generated for {subnet}")
            return

        # Phase 1: Execute initial commands through proxy
        with print_lock:
            print(f"[{thread_id}] Phase 1: Host discovery and port scanning...")
        xml_results = execute_commands(subnet, commands, subdir,
                                      use_proxy=use_proxy,
                                      proxychains_config=proxychains_config)
        json_results = convert_xml_to_json(xml_results)

        # Phase 2: Extract ports and scan services
        if json_results:
            with print_lock:
                print(f"[{thread_id}] Phase 2: Extracting ports...")
            ports = extract_ports_from_json(json_results)

            if ports:
                with print_lock:
                    print(f"[{thread_id}] [✓] Ports: {', '.join(sorted(ports, key=lambda x: int(x)))}")

                # Generate and execute service detection command
                service_command = generate_service_command(subnet, ports)
                if service_command:
                    with print_lock:
                        print(f"[{thread_id}] Phase 3: Detecting services...")
                    service_xml_results = execute_commands(subnet, [service_command], subdir,
                                                          use_proxy=use_proxy,
                                                          proxychains_config=proxychains_config)
                    service_json_results = convert_xml_to_json(service_xml_results)
                    json_results.extend(service_json_results)
            else:
                with print_lock:
                    print(f"[{thread_id}] [!] No open ports found")

        # Analyze results with Claude
        if json_results:
            with print_lock:
                print(f"[{thread_id}] Analyzing with AI...")
            summary = analyze_results(json_results)

            # Save results
            try:
                with open(os.path.join(subdir, "summary.json"), "w") as f:
                    json.dump(json_results, f, indent=2)
                with open(os.path.join(subdir, "analysis.txt"), "w") as f:
                    f.write(summary)

                duration = datetime.now() - start_time
                with print_lock:
                    print(f"[{thread_id}] [✓] Completed in {duration.total_seconds():.1f}s")
                    print(f"[{thread_id}] Results: {subdir}")
            except Exception as e:
                with print_lock:
                    print(f"[{thread_id}] [!] Error saving: {e}")
        else:
            with print_lock:
                print(f"[{thread_id}] [!] No results obtained")

    except Exception as e:
        with print_lock:
            print(f"[{thread_id}] [!] Error: {e}")


# MAIN: Execute remote scans through SSH tunnel
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  SCAN-AI - Remote Network Scanning via SSH Tunnel")
    print(f"{'='*60}")
    print(f"SSH Target: {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
    print(f"SOCKS Port: {SOCKS_PORT}")
    print(f"Target subnets: {len(SUBNETS)}")
    for subnet in SUBNETS:
        print(f"  - {subnet}")
    print(f"{'='*60}\n")

    # Initialize SSH tunnel
    tunnel = SSHTunnel(
        ssh_host=SSH_HOST,
        ssh_user=SSH_USER,
        ssh_port=SSH_PORT,
        local_port=SOCKS_PORT,
        ssh_key=SSH_KEY
    )

    try:
        # Start SSH tunnel
        if not tunnel.start():
            print("[!] Failed to establish SSH tunnel. Exiting.")
            exit(1)

        # Test tunnel
        print("[*] Testing SSH tunnel...")
        if test_tunnel(target_host=SSH_HOST, socks_port=SOCKS_PORT):
            print("[✓] Tunnel is working correctly\n")
        else:
            print("[!] Warning: Tunnel test failed, but continuing...\n")

        # Create proxychains config
        proxychains_conf = create_proxychains_config(socks_port=SOCKS_PORT)
        if not proxychains_conf:
            print("[!] Failed to create proxychains config. Exiting.")
            tunnel.stop()
            exit(1)

        print()
        total_start = datetime.now()

        # Create threads for each subnet
        threads = []
        for i, subnet in enumerate(SUBNETS):
            thread = threading.Thread(
                target=scan_subnet,
                args=(subnet, True, proxychains_conf),  # use_proxy=True
                name=f"Thread-{i+1}"
            )
            threads.append(thread)
            thread.start()

        # Wait for all to finish
        for thread in threads:
            thread.join()

        total_duration = datetime.now() - total_start

        print(f"\n{'='*60}")
        print(f"[*] All scans completed")
        print(f"[*] Total time: {total_duration.total_seconds():.1f}s")
        print(f"[*] Results in: ./{BASE_DIR}/")
        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
    finally:
        # Always close the SSH tunnel
        print("\n[*] Closing SSH tunnel...")
        tunnel.stop()
        print("[✓] Done")
