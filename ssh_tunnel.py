# middleware/ssh_tunnel.py
# Manages SSH tunnels and SOCKS proxy for remote scanning

import subprocess
import time
import os
import signal


class SSHTunnel:
    """
    Manages SSH dynamic port forwarding (SOCKS proxy) for remote network scanning
    """

    def __init__(self, ssh_host, ssh_user, ssh_port=22, local_port=1080, ssh_key=None):
        """
        Initialize SSH tunnel configuration

        Args:
            ssh_host: SSH server hostname/IP
            ssh_user: SSH username
            ssh_port: SSH server port (default: 22)
            local_port: Local SOCKS proxy port (default: 1080)
            ssh_key: Path to SSH private key (optional)
        """
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_port = ssh_port
        self.local_port = local_port
        self.ssh_key = ssh_key
        self.process = None

    def start(self):
        """
        Start SSH dynamic port forwarding tunnel
        Creates a SOCKS proxy on localhost:local_port
        """
        # Build SSH command
        cmd = [
            "ssh",
            "-D", str(self.local_port),  # Dynamic port forwarding
            "-f",  # Background
            "-N",  # No remote command
            "-q",  # Quiet mode
            "-p", str(self.ssh_port),
        ]

        # Add SSH key if provided
        if self.ssh_key:
            cmd.extend(["-i", self.ssh_key])

        # Add compression for better performance
        cmd.extend(["-C"])

        # Target host
        cmd.append(f"{self.ssh_user}@{self.ssh_host}")

        try:
            print(f"[*] Starting SSH tunnel to {self.ssh_user}@{self.ssh_host}:{self.ssh_port}")
            print(f"[*] SOCKS proxy: localhost:{self.local_port}")

            # Execute SSH command
            subprocess.run(cmd, check=True)

            # Wait for tunnel to establish
            time.sleep(2)

            print("[✓] SSH tunnel established")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[!] Error starting SSH tunnel: {e}")
            return False
        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            return False

    def stop(self):
        """
        Stop SSH tunnel by killing the SSH process
        """
        try:
            # Find and kill SSH process using the dynamic port
            cmd = f"pkill -f 'ssh.*-D {self.local_port}'"
            subprocess.run(cmd, shell=True)
            print("[✓] SSH tunnel closed")
        except Exception as e:
            print(f"[!] Error closing tunnel: {e}")

    def is_active(self):
        """
        Check if SSH tunnel is active
        """
        try:
            cmd = f"pgrep -f 'ssh.*-D {self.local_port}'"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            return result.returncode == 0
        except:
            return False


def create_proxychains_config(socks_port=1080, config_path="/tmp/proxychains.conf"):
    """
    Create a proxychains configuration file

    Args:
        socks_port: SOCKS proxy port
        config_path: Path where to save config file

    Returns:
        Path to created config file
    """
    config = f"""# Proxychains config for scan-ai
# Generated automatically

strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 {socks_port}
"""

    try:
        with open(config_path, 'w') as f:
            f.write(config)
        print(f"[✓] Proxychains config created: {config_path}")
        return config_path
    except Exception as e:
        print(f"[!] Error creating proxychains config: {e}")
        return None


def test_tunnel(target_host="8.8.8.8", socks_port=1080):
    """
    Test if SSH tunnel is working by trying to reach a target through it

    Args:
        target_host: Host to test connectivity
        socks_port: SOCKS proxy port

    Returns:
        True if tunnel is working, False otherwise
    """
    try:
        # Use curl through SOCKS proxy to test
        cmd = f"curl -s --socks5 localhost:{socks_port} --connect-timeout 5 {target_host}"
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        return result.returncode == 0
    except:
        return False
