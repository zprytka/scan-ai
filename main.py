# middleware/main.py
# Entry point: Orchestrates the complete flow

from planner import plan_with_claude
from executor import execute_commands
from parser import convert_xml_to_json
from analyzer import analyze_results
from port_extractor import extract_ports_from_json, generate_service_command
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


SUBNETS = [
    "192.168.0.1/24"
]


BASE_DIR = "output"
os.makedirs(BASE_DIR, exist_ok=True)

# Lock to synchronize console output
print_lock = threading.Lock()


def scan_subnet(subnet):
    """
    Function that executes a complete subnet scan
    Runs in a separate thread for parallel processing
    """
    thread_id = threading.current_thread().name

    with print_lock:
        print(f"\n[{thread_id}] Starting scan of {subnet}")

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

        # Phase 1: Execute initial commands
        with print_lock:
            print(f"[{thread_id}] Phase 1: Host discovery and port scanning...")
        xml_results = execute_commands(subnet, commands, subdir)
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
                    service_xml_results = execute_commands(subnet, [service_command], subdir)
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


# MAIN: Execute parallel scans
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  SCAN-AI - Parallel Network Scanning with AI")
    print(f"{'='*60}")
    print(f"Target subnets: {len(SUBNETS)}")
    for subnet in SUBNETS:
        print(f"  - {subnet}")
    print(f"{'='*60}\n")

    total_start = datetime.now()

    # Create threads for each subnet
    threads = []
    for i, subnet in enumerate(SUBNETS):
        thread = threading.Thread(
            target=scan_subnet,
            args=(subnet,),
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
    print(f"[*] Results in: ./output/")
    print(f"{'='*60}\n")