#!/bin/bash

set -e

# ALEX Canisterid
ALEX_CANISTER_ID="7hcrm-4iaaa-aaaak-akuka-cai"
LBRY_CANISTER_ID="hdtfn-naaaa-aaaam-aciva-cai"

# Function to fetch blocks for a given canister
fetch_blocks() {
    local canister_id=$1
    local output_file=$2
    local temp_file="${output_file}.tmp"
    local start=0
    local length=1000
    
    # Initialize the output file with an empty array
    echo "[]" > "$output_file"
    
    while true; do
        echo "Fetching blocks $start to $((start + length - 1)) for $canister_id"
        
        # Fetch blocks and save to temp file
        if ! dfx canister call "$canister_id" icrc3_get_blocks "(vec { record { start = $start; length = $length } })" --network ic --output json | sed 's/^(//;s/)$//' | jq '.blocks' > "$temp_file"; then
            echo "Error fetching blocks for $canister_id. Exiting."
            exit 1
        fi
        
        # Check if we received any blocks
        block_count=$(jq length "$temp_file")
        
        if [ "$block_count" -eq 0 ]; then
            echo "No more blocks to fetch for $canister_id"
            break
        fi
        
        # Append new blocks to the output file
        if ! jq -s '.[0] + .[1]' "$output_file" "$temp_file" > "${output_file}" && mv "${output_file}" "$output_file"; then
            echo "Error appending blocks to $output_file. Exiting."
            exit 1
        fi
        
        # Update start for the next iteration
        start=$((start + block_count))
        
        # Optional: Add a small delay to avoid overwhelming the canister
        sleep 1
    done
    
    # Remove temporary file
    rm -f "$temp_file"
    
    echo "Blocks for $canister_id saved to $output_file"
}

# Create a directory for the output files
mkdir -p get_data

# Fetch blocks for ALEX
fetch_blocks "$ALEX_CANISTER_ID" "get_data/alex_blocks.json"

# Fetch blocks for LBRY
fetch_blocks "$LBRY_CANISTER_ID" "get_data/lbry_blocks.json"

echo "All blocks have been fetched and saved in the get_data directory."
