# middleware/parser.py
# Converts XML to JSON for each result

import xmltodict
import os


def convert_xml_to_json(file_list):
    """
    Converts nmap XML files to JSON format

    Args:
        file_list: List of paths to XML files

    Returns:
        List of dictionaries with parsed data
    """
    results = []

    for file in file_list:
        try:
            if not os.path.exists(file):
                print(f"[!] File not found: {file}")
                continue

            if os.path.getsize(file) == 0:
                print(f"[!] Empty file: {file}")
                continue

            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                doc = xmltodict.parse(content)
                results.append(doc)
                print(f"[✓] Parsed: {file}")

        except xmltodict.expat.ExpatError as e:
            print(f"[!] Error parsing XML in {file}: {e}")
        except Exception as e:
            print(f"[!] Error reading {file}: {e}")

    return results
