import sys
import os
import bisect

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
    """
    Calculate the amount of LBRY burned and current block reward based on total ALEX supply.
    
    :param total_alex_supply: Total supply of ALEX tokens as whole numbers
    :return: Tuple (lbry_burned, current_block_reward)
    """
    lbry_burned = 0
    alex_minted = 0
    
    for i, threshold in enumerate(LBRY_THRESHOLDS):
        reward = ALEX_PER_THRESHOLD[i]
        alex_per_lbry = reward * 3 / 10000  # ALEX minted per LBRY burned
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
        # If we've reached here, all ALEX has been minted
        lbry_burned = LBRY_THRESHOLDS[-1]
        current_block_reward = ALEX_PER_THRESHOLD[-1]
    
    return round(lbry_burned), current_block_reward

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 backup_tokenomics.py <total_alex_supply>")
        sys.exit(1)

    try:
        total_alex_supply = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid input '{sys.argv[1]}'. Expected an integer.")
        sys.exit(1)

    lbry_burned, current_reward = calculate_tokenomics(total_alex_supply)

    # Create the tokenomics_backup.txt file in the current directory
    output_file = os.path.join(os.path.dirname(__file__), "tokenomics_backup.txt")
    with open(output_file, "w") as f:
        f.write(f"Total ALEX supply: {total_alex_supply} ALEX\n")
        f.write(f"LBRY burned: {lbry_burned} LBRY\n")
        f.write(f"Current block reward: {current_reward} (represents {current_reward/10000:.4f} ALEX)\n")

    print(f"Tokenomics backup created successfully in {output_file}")
