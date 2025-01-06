import json
import os
import sys
from decimal import Decimal
import re

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

def parse_stakes_file(stakes_file):
    try:
        with open(stakes_file, 'r') as f:
            content = f.read()
        
        # Parse the stakes data using regex
        stakes = {}
        # Updated pattern to match Candid format with underscores and explicit type annotations
        pattern = r'principal\s+"([^"]+)".*?time\s+=\s+(\d+(?:_\d+)*)\s*:\s*nat64;\s*reward_icp\s+=\s+(\d+(?:_\d+)*)\s*:\s*nat64;\s*amount\s+=\s+(\d+(?:_\d+)*)\s*:\s*nat64'
        
        matches = re.finditer(pattern, content)
        for match in matches:
            principal = match.group(1)
            time = int(match.group(2).replace('_', ''))
            reward_icp = int(match.group(3).replace('_', ''))
            amount = int(match.group(4).replace('_', ''))
            # Convert amount to ALEX (divide by 10^8)
            amount_alex = Decimal(amount) / Decimal('100000000')
            stakes[principal] = {
                'amount': amount_alex,
                'reward_icp': reward_icp,
                'time': time
            }
        
        if not stakes:
            print("Warning: No stakes were parsed from the file. Content:")
            print(content[:500])  # Print first 500 chars for debugging
            
        return stakes
    except Exception as e:
        print(f"Error parsing stakes file: {e}")
        print(f"File contents:")
        with open(stakes_file, 'r') as f:
            print(f.read()[:500])  # Print first 500 chars for debugging
        sys.exit(1)

def write_backup(total_alex_supply, icp_available, stakes, output_file):
    lbry_burned, current_block_reward = calculate_tokenomics(total_alex_supply)
    total_staked = sum(stake['amount'] for stake in stakes.values())

    try:
        with open(output_file, 'w') as f:
            f.write("Tokenomics:\n")
            f.write(f"Total ALEX supply: {total_alex_supply} ALEX\n")
            f.write(f"LBRY burned: {lbry_burned} LBRY\n")
            f.write(f"Current block reward: {current_block_reward} (represents {current_block_reward/10000:.4f} ALEX)\n\n")
            
            f.write("ICP Swap:\n")
            f.write(f"Total staked: {total_staked:.8f} ALEX\n")
            f.write(f"ICP available: {icp_available} ICP\n")
            f.write("\nStakes:\n")
            for principal, data in stakes.items():
                f.write(f"  {principal}:\n")
                f.write(f"    Amount: {data['amount']:.8f} ALEX\n")
                f.write(f"    Reward ICP: {data['reward_icp']}\n")

        print(f"Backup saved to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 backup.py <total_alex_supply> <icp_available> <stakes_file>")
        sys.exit(1)

    try:
        total_alex_supply = int(sys.argv[1])
        icp_available = Decimal(sys.argv[2])
        stakes_file = sys.argv[3]
    except ValueError:
        print(f"Error: Invalid input. Expected integers for total_alex_supply and icp_available.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "backup.txt")

    stakes = parse_stakes_file(stakes_file)
    write_backup(total_alex_supply, icp_available, stakes, output_file)

if __name__ == "__main__":
    main()
