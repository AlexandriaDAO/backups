# dfx canister call fjqb7-6qaaa-aaaak-qc7gq-cai icrc7_tokens '(opt 0, opt 10)' > tokens_output.txt

# dfx canister call icrc7 icrc7_owner_of '(vec {101; 102; 103})' > owners_output.txt

# dfx canister call icrc7 icrc7_token_metadata '(vec {101; 102; 103})' > metadata_output.txt

#!/bin/bash

# Set variables for your main project
NETWORK="ic"
CANISTER_ID="uxyan-oyaaa-aaaap-qhezq-cai"
BATCH_SIZE=1
OUTPUT_FILE="combined_output.txt"

# Function to run dfx command
run_dfx() {
    dfx canister call $CANISTER_ID "$@" --network $NETWORK
}

# Function to process tokens
process_tokens() {
    local start_index=$1
    local amount=$BATCH_SIZE
    local total_processed=0

    > "$OUTPUT_FILE"  # Clear the output file

    while true; do
        echo "Processing tokens starting from index $start_index, amount $amount..."
        
        # Get token IDs
        local tokens_response=$(run_dfx "icrc7_tokens" "(opt $start_index, opt $amount)")
        
        # Check if we've reached the end of the collection
        if [[ $tokens_response == *"(vec {})"* ]]; then
            echo "Reached the end of the collection. Total tokens processed: $total_processed"
            break
        fi

        # Extract and process token IDs
        echo "$tokens_response" | grep -E '[0-9_]+ : nat;' | sed -E 's/^[[:space:]]*([0-9_]+) : nat;$/\1/' |
        while read -r token_id; do
            echo "Token ID: $token_id" >> "$OUTPUT_FILE"
            owner=$(run_dfx "icrc7_owner_of" "(vec {$token_id;})" | grep -oP 'owner = principal "\K[^"]+')
            echo "Owner: $owner" >> "$OUTPUT_FILE"
            metadata=$(run_dfx "icrc7_token_metadata" "(vec {$token_id;})" | grep -oP '(?<=\{)[^}]+(?=\})')
            echo "Metadata: $metadata" >> "$OUTPUT_FILE"
            echo "---" >> "$OUTPUT_FILE"
            ((total_processed++))
        done

        # Move to the next batch
        start_index=$((start_index + amount))
    done

    echo "Backup complete. Results are in $OUTPUT_FILE"
}

# Main execution
echo "Starting backup of entire token collection..."
process_tokens 0