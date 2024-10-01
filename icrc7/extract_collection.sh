# dfx canister call icrc7 icrc7_tokens '(opt 0, opt 10)' > tokens_output.txt

# dfx canister call icrc7 icrc7_owner_of '(vec {101; 102; 103})' > owners_output.txt

# dfx canister call icrc7 icrc7_token_metadata '(vec {101; 102; 103})' > metadata_output.txt


#!/bin/bash

# Set variables for your main project
NETWORK="local"
CANISTER_ID="fjqb7-6qaaa-aaaak-qc7gq-cai"

# Function to run dfx command
run_dfx() {
    dfx canister call $CANISTER_ID "$@" --network $NETWORK
}

# Function to process tokens in batches
process_tokens() {
    local start=$1
    local end=$2
    local batch_size=10
    
    for ((i=start; i<=end; i+=batch_size)); do
        local batch_end=$((i + batch_size - 1))
        [[ $batch_end -gt $end ]] && batch_end=$end
        
        echo "Processing tokens $i to $batch_end..."
        
        # Get token IDs
        run_dfx "icrc7_tokens" "(opt $i, opt $((batch_end - i + 1)))" > temp_tokens.txt
        
        # Extract and process token IDs
        grep -E '[0-9_]+ : nat;' temp_tokens.txt | sed -E 's/^[[:space:]]*([0-9_]+) : nat;$/\1/' > temp_numbers.txt
        
        # Build input vector
        local input_vec="(vec {"
        while IFS= read -r num; do
            input_vec+="$num;"
        done < temp_numbers.txt
        input_vec="${input_vec%;}})"
        
        # Get owners and metadata
        run_dfx "icrc7_owner_of" "$input_vec" >> owners_output.txt
        run_dfx "icrc7_token_metadata" "$input_vec" >> metadata_output.txt
    done
    
    rm temp_tokens.txt temp_numbers.txt
}

# Main execution
echo "Enter the start token number:"
read start_token

echo "Enter the end token number:"
read end_token

# Clear previous output files
> owners_output.txt
> metadata_output.txt

# Process tokens
process_tokens $start_token $end_token

echo "Processing complete. Results are in owners_output.txt and metadata_output.txt"