# Scan-AI - Automated Pentesting Tool

Automated network reconnaissance tool that uses AI to plan, execute, and analyze network scans with Nmap/RustScan.

## Features

- **Parallel scanning**: Multiple subnets simultaneously with threading
- **Intelligent planning**: Scan planning using Claude AI
- **Stealth scanning**: Uses `--min-rate 500` to avoid detection
- **Dynamic scanning**: Only scans services on found open ports
- **AI analysis**: Automatically identifies vulnerabilities and risks
- **Complete reports**: Generates structured JSON and text analysis
- **Robust error handling** and input validation
- **Real-time feedback** with thread identification

## Requirements

- Python 3.8+
- nmap installed on the system
- Claude API key (Anthropic)
- **For remote scanning**:
  - proxychains4
  - SSH access to remote network

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install nmap (Ubuntu/Debian)
sudo apt-get install nmap

# For remote scanning, install proxychains
sudo apt-get install proxychains4

# Configure API key
cp .env.example .env
# Edit .env and add your CLAUDE_API_KEY
```

## Configuration

1. Get a Claude API key at https://console.anthropic.com/
2. Configure the environment variable:

```bash
export CLAUDE_API_KEY="your_api_key_here"
```

3. Edit `main.py` to configure the subnets to scan:

```python
SUBNETS = [
    "192.168.5.64/27",
    "192.168.5.128/27",
    "192.168.5.32/27",
    "192.168.5.96/27",
    "192.168.5.0/27"
]
```

**Note**: You can add as many subnets as you want. They will **all be scanned in parallel**.

## Usage

### Local Network Scanning

```bash
python3 main.py
```

### Remote Network Scanning (via SSH Tunnel)

For scanning remote networks through SSH:

1. Edit `main_remote.py` and configure:

```python
# SSH Tunnel Configuration
SSH_HOST = "your.ssh.server.com"
SSH_USER = "username"
SSH_PORT = 22
SSH_KEY = "/path/to/ssh/key"  # Optional

# Target remote subnets
SUBNETS = [
    "10.0.0.0/24",      # Internal network
    "172.16.0.0/24"     # DMZ network
]
```

2. Run the remote scanner:

```bash
python3 main_remote.py
```

The tool will:
- Automatically create an SSH tunnel with dynamic port forwarding
- Configure proxychains to route traffic through the tunnel
- Execute all nmap commands through the SOCKS proxy
- Close the tunnel when finished

### Example output:

```
============================================================
  SCAN-AI - Parallel Network Scanning with AI
============================================================
Target subnets: 5
  - 192.168.5.64/27
  - 192.168.5.128/27
  - 192.168.5.32/27
  - 192.168.5.96/27
  - 192.168.5.0/27
============================================================

[Thread-1] Starting scan of 192.168.5.64/27
[Thread-2] Starting scan of 192.168.5.128/27
[Thread-3] Starting scan of 192.168.5.32/27
...
```

Results will be saved in the `output/` directory organized by subnet:

```
output/
├── 192.168.5.0_27/
│   ├── scan_0.xml (ping sweep)
│   ├── scan_1.xml (port scan)
│   ├── scan_2.xml (service detection)
│   ├── summary.json
│   └── analysis.txt
├── 192.168.5.32_27/
│   └── ...
└── ...
```

## Architecture

- **main.py**: Local network scanning orchestrator
- **main_remote.py**: Remote network scanning via SSH tunnel
- **planner.py**: Generates stealthy scan plan using Claude AI
- **executor.py**: Executes nmap commands with timeout, error handling, and proxy support
- **parser.py**: Safely converts XML to JSON
- **port_extractor.py**: Extracts open ports and generates dynamic commands
- **analyzer.py**: Analyzes results with AI to identify vulnerabilities
- **ssh_tunnel.py**: Manages SSH tunnels and SOCKS proxy configuration

## Workflow

1. **Planning**: Claude generates optimized nmap commands
2. **Phase 1**: Active host discovery (`-sn`)
3. **Phase 2**: Complete port scan (`-p- --min-rate 500`)
4. **Phase 3**: Service detection only on open ports (`-sV -sC`)
5. **Analysis**: Claude analyzes all results and identifies risks
6. **Reports**: Generates JSON and plain text analysis

## Security

This tool is designed ONLY for defensive and authorized use. Security features:

- No use of `eval()` for parsing responses
- CIDR network input validation
- Command timeouts (5 minutes)
- Complete exception handling
- Error logging

## Important Notes

- Only use this tool on networks you have authorization to scan
- Scans can be detected by security systems
- Review local laws regarding pentesting before use

## Remote Scanning via SSH

### How it works:

1. **SSH Dynamic Port Forwarding**: Creates a SOCKS5 proxy
   ```bash
   ssh -D 1080 -f -N user@remote-server
   ```

2. **Proxychains Integration**: Routes nmap through the tunnel
   ```bash
   proxychains4 nmap -sV -sC target
   ```

3. **Automatic Management**: The tool handles tunnel lifecycle

### Use Cases:

- ✅ Scan internal networks from outside
- ✅ Pivot through compromised/authorized hosts
- ✅ Test from different geographical locations
- ✅ Bypass firewall restrictions (when authorized)
- ✅ Aggregate results from multiple vantage points

### SSH Tunnel Example:

```bash
# Manual setup (optional, tool does this automatically)
ssh -D 1080 -f -N -C user@jumphost.company.com

# Verify tunnel
curl --socks5 localhost:1080 http://internal-server

# Test with proxychains
proxychains4 nmap -sn 10.0.0.0/24
```

## Corrections Made

- Removed dangerous use of `eval()`
- Updated Claude model (claude-2.1 → claude-sonnet-4-5-20250929)
- Added error handling in all functions
- Fixed duplicate code between files
- Added network input validation
- Improved user feedback with visual indicators
- Added command timeouts
- Complete documentation and docstrings
- Translated entire project to English
- Added SSH tunnel support for remote scanning
- Integrated proxychains for SOCKS proxy routing
