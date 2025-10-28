#!/usr/bin/env python3
"""
Test SSH Tunnel - Quick test script for SSH tunnel functionality
"""

from ssh_tunnel import SSHTunnel, create_proxychains_config, test_tunnel
import sys


def main():
    print("="*60)
    print("  SSH Tunnel Test Tool")
    print("="*60)

    # Get SSH credentials
    ssh_host = input("SSH Host (e.g., example.com): ").strip()
    ssh_user = input("SSH User: ").strip()
    ssh_port = input("SSH Port [22]: ").strip() or "22"
    ssh_key = input("SSH Key path (optional, press Enter to skip): ").strip() or None
    socks_port = input("SOCKS Port [1080]: ").strip() or "1080"

    print()

    # Create tunnel
    tunnel = SSHTunnel(
        ssh_host=ssh_host,
        ssh_user=ssh_user,
        ssh_port=int(ssh_port),
        local_port=int(socks_port),
        ssh_key=ssh_key
    )

    try:
        # Start tunnel
        if not tunnel.start():
            print("[!] Failed to start tunnel")
            return 1

        # Check if active
        if tunnel.is_active():
            print("[✓] Tunnel is active")
        else:
            print("[!] Tunnel appears inactive")
            return 1

        # Test connectivity
        print("\n[*] Testing tunnel connectivity...")
        if test_tunnel(target_host=ssh_host, socks_port=int(socks_port)):
            print("[✓] Tunnel is working!")
        else:
            print("[!] Tunnel test failed")

        # Create proxychains config
        print("\n[*] Creating proxychains config...")
        config = create_proxychains_config(socks_port=int(socks_port))
        if config:
            print(f"[✓] Config created: {config}")
            print("\nYou can now use:")
            print(f"  proxychains4 -f {config} nmap -sn <target>")

        print("\n[*] Tunnel is ready. Press Ctrl+C to close...")
        input()

    except KeyboardInterrupt:
        print("\n\n[*] Closing tunnel...")
    except Exception as e:
        print(f"\n[!] Error: {e}")
    finally:
        tunnel.stop()
        print("[✓] Done")

    return 0


if __name__ == "__main__":
    sys.exit(main())
