import json
import os
import sys
from datetime import datetime, timezone

def nanoseconds_to_iso(ns):
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat()

def format_amount(amount):
    return f"{int(amount) / 1e8:.8f} LBRY"

def blob_to_hex(blob):
    return ''.join(f'{b:02x}' for b in blob)

def process_blocks(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    processed_blocks = []

    for block in data:  # Changed this line
        block_data = block['block']['Map']
        tx_data = next(item['1']['Map'] for item in block_data if item['0'] == 'tx')
        
        processed_block = {
            'id': block['id'],
            'timestamp': nanoseconds_to_iso(int(next(item['1']['Nat'] for item in block_data if item['0'] == 'ts'))),
            'operation': next(item['1']['Text'] for item in tx_data if item['0'] == 'op'),
        }

        # Add amount if it exists
        amount = next((item['1']['Nat'] for item in tx_data if item['0'] == 'amt'), None)
        if amount:
            processed_block['amount'] = format_amount(amount)

        for field in ['to', 'from', 'spender']:
            value = next((item['1']['Array'][0]['Blob'] for item in tx_data if item['0'] == field), None)
            if value:
                processed_block[field] = blob_to_hex(value)

        fee = next((item['1']['Nat'] for item in block_data if item['0'] == 'fee'), None)
        if fee:
            processed_block['fee'] = format_amount(fee)

        processed_blocks.append(processed_block)

    with open(output_file, 'w') as f:
        json.dump(processed_blocks, f, indent=2)

    print(f"Processed {len(processed_blocks)} blocks. Output saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Process LBRY blocks
    lbry_input_file = os.path.join(script_dir, "lbry_blocks.json")
    lbry_output_file = os.path.join(script_dir, "processed_lbry_blocks.json")
    process_blocks(lbry_input_file, lbry_output_file)

    # Process ALEX blocks
    alex_input_file = os.path.join(script_dir, "alex_blocks.json")
    alex_output_file = os.path.join(script_dir, "processed_alex_blocks.json")
    process_blocks(alex_input_file, alex_output_file)
