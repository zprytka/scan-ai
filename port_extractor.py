# middleware/port_extractor.py
# Extracts open ports from nmap XML results

import os


def extract_ports_from_json(json_results):
    """
    Extracts all open ports from parsed results

    Args:
        json_results: List of dictionaries with nmap results

    Returns:
        Set of unique ports found
    """
    ports = set()

    for result in json_results:
        try:
            # Navigate nmap XML -> JSON structure
            nmaprun = result.get('nmaprun', {})
            hosts = nmaprun.get('host', [])

            # If single host, it comes as dict, not list
            if isinstance(hosts, dict):
                hosts = [hosts]

            for host in hosts:
                ports_data = host.get('ports', {})
                ports_list = ports_data.get('port', [])

                # If single port, it comes as dict
                if isinstance(ports_list, dict):
                    ports_list = [ports_list]

                for port in ports_list:
                    state = port.get('state', {})
                    if state.get('@state') == 'open':
                        port_id = port.get('@portid')
                        if port_id:
                            ports.add(port_id)

        except Exception as e:
            print(f"[!] Error extracting ports: {e}")
            continue

    return ports


def generate_service_command(subnet, ports):
    """
    Generates nmap command to scan services on specific ports

    Args:
        subnet: The target subnet
        ports: Set or list of ports

    Returns:
        Nmap command as string
    """
    if not ports:
        return None

    # Sort ports and convert to comma-separated string
    ports_str = ','.join(sorted(ports, key=lambda x: int(x)))

    # Generate command with found ports
    command = f"nmap -sV -sC -p{ports_str} {subnet}"

    return command
