import json
import os
import sys
from decimal import Decimal

# Constants from your setup
LBRY_THRESHOLDS = [
    21_000, 42_000, 84_000, 168_000, 336_000, 672_000, 1_344_000, 2_688_000,
    5_376_000, 10_752_000, 21_504_000, 43_008_000, 86_016_000, 172_032_000,
    344_064_000, 688_128_000, 1_376_256_000, 61632592000
]

ALEX_PER_THRESHOLD = [
    50_000, 25_000, 12_500, 6_250, 3_125, 1_562, 781, 391,
    195, 98, 49, 24, 12, 6, 3, 2, 1, 1
]

def calculate_tokenomics(total_alex_supply):
    lbry_burned = 0
    alex_minted = 0
    
    for i, threshold in enumerate(LBRY_THRESHOLDS):
        reward = ALEX_PER_THRESHOLD[i]
        alex_per_lbry = reward * 3 / 10000
        lbry_in_phase = threshold - (0 if i == 0 else LBRY_THRESHOLDS[i-1])
        alex_in_phase = lbry_in_phase * alex_per_lbry
        
        if alex_minted + alex_in_phase >= total_alex_supply:
            remaining_alex = total_alex_supply - alex_minted
            lbry_burned += remaining_alex / alex_per_lbry
            current_block_reward = ALEX_PER_THRESHOLD[i]
            break
        
        lbry_burned += lbry_in_phase
        alex_minted += alex_in_phase
    else:
        lbry_burned = LBRY_THRESHOLDS[-1]
        current_block_reward = ALEX_PER_THRESHOLD[-1]
    
    return round(lbry_burned), current_block_reward

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

def write_backup(total_alex_supply, icp_available, stakes, output_file):
    lbry_burned, current_block_reward = calculate_tokenomics(total_alex_supply)
    total_staked = sum(stakes.values())

    try:
        with open(output_file, 'w') as f:
            f.write("Tokenomics:\n")
            f.write(f"Total ALEX supply: {total_alex_supply} ALEX\n")
            f.write(f"LBRY burned: {lbry_burned} LBRY\n")
            f.write(f"Current block reward: {current_block_reward} (represents {current_block_reward/10000:.4f} ALEX)\n\n")
            
            f.write("ICP Swap:\n")
            f.write(f"Total staked: {total_staked}\n")
            f.write(f"ICP available: {icp_available}\n")
            f.write("Stakes:\n")
            for user, amount in stakes.items():
                f.write(f"  {user}: {amount}\n")

        print(f"Backup saved to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 backup.py <total_alex_supply> <icp_available>")
        sys.exit(1)

    try:
        total_alex_supply = int(sys.argv[1])
        icp_available = Decimal(sys.argv[2])
    except ValueError:
        print(f"Error: Invalid input. Expected integers for total_alex_supply and icp_available.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "./get_data/processed_alex_blocks.json")
    output_file = os.path.join(script_dir, "backup.txt")

    processed_blocks = read_processed_blocks(input_file)
    cleaned_transactions = clean_transactions(processed_blocks)
    stakes = calculate_stakes(cleaned_transactions)
    write_backup(total_alex_supply, icp_available, stakes, output_file)

if __name__ == "__main__":
    main()
