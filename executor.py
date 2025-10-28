# middleware/executor.py
# Executes given commands and saves XML in assigned subfolder

import subprocess
import os


def execute_commands(subnet, commands, output_path, use_proxy=False, proxychains_config=None):
    """
    Executes a list of scan commands and saves results in XML

    Args:
        subnet: The target subnet
        commands: List of commands to execute
        output_path: Directory where to save results
        use_proxy: Whether to use proxychains (default: False)
        proxychains_config: Path to proxychains config file

    Returns:
        List of generated XML files
    """
    files = []

    if not commands:
        print("[!] No commands to execute")
        return files

    for i, cmd in enumerate(commands):
        # Define output filenames
        xml_file = os.path.join(output_path, f"scan_{i}.xml")
        nmap_file = os.path.join(output_path, f"scan_{i}.nmap")
        gnmap_file = os.path.join(output_path, f"scan_{i}.gnmap")

        # Build command with multiple output formats
        # -oX: XML output (for parsing)
        # -oN: Normal nmap output (human readable)
        # -oG: Grepable output (for grep/awk)
        output_args = f"-oX {xml_file} -oN {nmap_file} -oG {gnmap_file}"

        # Add proxychains if requested
        if use_proxy:
            if proxychains_config:
                final_cmd = f"proxychains4 -f {proxychains_config} {cmd} {output_args}"
            else:
                final_cmd = f"proxychains4 {cmd} {output_args}"
        else:
            final_cmd = f"{cmd} {output_args}"

        print(f"[cmd] Executing: {final_cmd}")

        try:
            result = subprocess.run(
                final_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                if os.path.exists(xml_file) and os.path.getsize(xml_file) > 0:
                    files.append(xml_file)
                    print(f"[✓] Scan {i} completed:")
                    print(f"    - XML:      {xml_file}")
                    if os.path.exists(nmap_file):
                        print(f"    - Normal:   {nmap_file}")
                    if os.path.exists(gnmap_file):
                        print(f"    - Grepable: {gnmap_file}")
                else:
                    print(f"[!] Warning: File {xml_file} is empty or doesn't exist")
            else:
                print(f"[!] Error in command {i}: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"[!] Timeout in command {i}: {final_cmd}")
        except Exception as e:
            print(f"[!] Exception executing command {i}: {e}")

    return files
