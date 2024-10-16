import json
import os
import sys
from datetime import datetime, timezone

def nanoseconds_to_iso(ns):
    seconds = ns / 1_000_000_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()

def format_amount(amount):
    return f"{int(amount) / 1_000_000_000:.8f} ALEX"

def blob_to_hex(blob):
    return ''.join(f'{b:02x}' for b in blob)

def process_blocks(input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Unable to parse '{input_file}' as JSON.")
        sys.exit(1)

    processed_blocks = []

    for block in data['blocks']:
        block_data = block['block']['Map']
        tx_data = next(item['1']['Map'] for item in block_data if item['0'] == 'tx')
        
        processed_block = {
            'id': block['id'],
            'timestamp': nanoseconds_to_iso(int(next(item['1']['Nat'] for item in block_data if item['0'] == 'ts'))),
            'operation': next(item['1']['Text'] for item in tx_data if item['0'] == 'op'),
            'amount': format_amount(next(item['1']['Nat'] for item in tx_data if item['0'] == 'amt')),
        }

        if 'to' in [item['0'] for item in tx_data]:
            processed_block['to'] = blob_to_hex(next(item['1']['Array'][0]['Blob'] for item in tx_data if item['0'] == 'to'))

        if 'from' in [item['0'] for item in tx_data]:
            processed_block['from'] = blob_to_hex(next(item['1']['Array'][0]['Blob'] for item in tx_data if item['0'] == 'from'))

        if 'spender' in [item['0'] for item in tx_data]:
            processed_block['spender'] = blob_to_hex(next(item['1']['Array'][0]['Blob'] for item in tx_data if item['0'] == 'spender'))

        if 'fee' in [item['0'] for item in block_data]:
            processed_block['fee'] = format_amount(next(item['1']['Nat'] for item in block_data if item['0'] == 'fee'))

        processed_blocks.append(processed_block)

    with open(output_file, 'w') as f:
        json.dump(processed_blocks, f, indent=2)

    print(f"Processed {len(processed_blocks)} blocks. Output saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input_file = os.path.join(script_dir, "blocks.json")
    default_output_file = os.path.join(script_dir, "processed_blocks.json")

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input_file

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = default_output_file

    process_blocks(input_file, output_file)
