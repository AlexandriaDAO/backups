import json
import os
import sys
from decimal import Decimal

def read_processed_blocks(input_file):
    try:
        with open(input_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Unable to parse '{input_file}' as JSON.")
        sys.exit(1)

def clean_transactions(transactions):
    staking_contract_address = "000000000170480a0101"
    cleaned = []
    for tx in transactions:
        if tx['operation'] == 'xfer' and (tx['to'] == staking_contract_address or tx['from'] == staking_contract_address):
            cleaned.append(tx)
    return cleaned

def calculate_stakes(transactions):
    stakes = {}
    for tx in transactions:
        amount = Decimal(tx['amount'].split()[0])
        if tx['to'] == "000000000170480a0101":  # Staking
            user = tx['from']
            stakes[user] = stakes.get(user, Decimal('0')) + amount
        else:  # Unstaking
            user = tx['to']
            stakes[user] = stakes.get(user, Decimal('0')) - amount
    return stakes

def write_stake_backup(stakes, icp_available, output_file):
    try:
        total_staked = sum(stakes.values())
        output_data = {
            "total_staked": str(total_staked),
            "icp_available": str(icp_available),
            "stakes": {user: str(amount) for user, amount in stakes.items()}
        }
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Stake backup saved to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input_file = os.path.join(script_dir, "./get_data/processed_alex_blocks.json")
    default_output_file = os.path.join(script_dir, "icp_swap_backup.txt")

    if len(sys.argv) < 2:
        print("Error: ICP balance not provided.")
        sys.exit(1)

    icp_available = Decimal(sys.argv[1])

    if len(sys.argv) > 2:
        input_file = sys.argv[2]
    else:
        input_file = default_input_file

    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    else:
        output_file = default_output_file

    processed_blocks = read_processed_blocks(input_file)
    cleaned_transactions = clean_transactions(processed_blocks)
    stakes = calculate_stakes(cleaned_transactions)
    write_stake_backup(stakes, icp_available, output_file)

if __name__ == "__main__":
    main()
