# dfx canister call fjqb7-6qaaa-aaaak-qc7gq-cai icrc7_tokens '(opt 0, opt 10)' > tokens_output.txt

# dfx canister call icrc7 icrc7_owner_of '(vec {101; 102; 103})' > owners_output.txt

# dfx canister call icrc7 icrc7_token_metadata '(vec {101; 102; 103})' > metadata_output.txt

#!/bin/bash

# Set variables for your main project
NETWORK="ic"
CANISTER_ID="uxyan-oyaaa-aaaap-qhezq-cai"
# Use a larger batch size for efficiency
BATCH_SIZE=100
OUTPUT_FILE="nft_data.json"

# Function to run dfx command and capture output/error with retries
run_dfx() {
    local max_retries=5
    local attempt=1
    local delay=2 # Initial delay in seconds
    local result
    local exit_code

    while [ $attempt -le $max_retries ]; do
        echo "Attempt $attempt/$max_retries: dfx canister --network $NETWORK call $CANISTER_ID \"$@\""
        # Capture stdout and stderr, and the exit code
        result=$(dfx canister --network "$NETWORK" call "$CANISTER_ID" "$@" 2>&1)
        exit_code=$?

        # Check if the command succeeded (exit code 0) and didn't contain common error patterns
        if [ $exit_code -eq 0 ] && ! echo "$result" | grep -qE 'Error:|Connection refused|503 Service Unavailable|no_healthy_nodes'; then
            echo "$result" # Output the successful result
            return 0 # Success
        fi

        # If it failed, print the error and wait before retrying
        echo "Command failed (Exit Code: $exit_code). Response:"
        echo "$result"
        if [ $attempt -lt $max_retries ]; then
            echo "Retrying in $delay seconds..."
            sleep $delay
            # Exponential backoff
            delay=$((delay * 2))
        fi
        ((attempt++))
    done

    # If all retries failed
    echo "Command failed after $max_retries attempts."
    echo "$result" # Output the last failed result
    return 1 # Failure
}

# Function to process tokens (Revised for batching and JSON output)
process_tokens() {
    local start_index=$1
    local batch_size=$BATCH_SIZE

    # Initialize output file
    echo "{" > "$OUTPUT_FILE"
    echo "\"tokens\": [" >> "$OUTPUT_FILE"

    local first_entry=true

    while true; do
        echo "Fetching batch starting at $start_index (size $batch_size)..."

        # Get batch of token IDs
        local tokens_response=$(run_dfx "icrc7_tokens" "(opt $start_index, opt $batch_size)")

        # Check for errors in fetching token IDs
        if echo "$tokens_response" | grep -q "Error:"; then
            echo "Error fetching token IDs batch starting at $start_index."
            echo "Response: $tokens_response"
            echo "Exiting due to error."
            # Clean up partial JSON
            echo "]}" >> "$OUTPUT_FILE"
            exit 1
        fi

        # If we get an empty vector, we're done
        if [[ $tokens_response == *"(vec {})"* ]]; then
            echo "Reached end of collection."
            break
        fi

        # Extract token IDs more carefully
        local tokens_content=$(echo "$tokens_response" | sed -n 's/.*vec {\(.*\)}.*/\1/p')
        local token_ids_list=$(echo "$tokens_content" | grep -oE '[0-9_]+')

        # If we got token IDs, get their metadata and owners in batch
        if [ -n "$token_ids_list" ]; then
            # Format them into a semicolon-separated string for Candid vec
            local semicolon_separated_ids=$(echo "$token_ids_list" | paste -sd ';')
            local vec_argument="(vec {$semicolon_separated_ids})"

            # Get metadata and ownership in single batch calls
            echo "Fetching metadata for tokens..." # Could count tokens here if needed
            local metadata_response=$(run_dfx "icrc7_token_metadata" "$vec_argument")
            echo "Fetching owners for tokens..."
            local owner_response=$(run_dfx "icrc7_owner_of" "$vec_argument")

            # Check for errors in metadata/owner calls
            if echo "$metadata_response" | grep -q "Error:" || echo "$owner_response" | grep -q "Error:"; then
                echo "Error fetching metadata or owners for batch starting at $start_index."
                echo "Token IDs vec: $vec_argument"
                echo "Metadata Response: $metadata_response"
                echo "Owner Response: $owner_response"
                echo "Skipping this batch due to error."
                start_index=$((start_index + batch_size))
                continue
            fi

            # Process and save the data
            if [ "$first_entry" = false ]; then
                echo "," >> "$OUTPUT_FILE"
            fi

            # Escape raw responses for JSON embedding
            local escaped_metadata=$(echo "$metadata_response" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g' -e 's/\t/\\t/g')
            local escaped_owners=$(echo "$owner_response" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g' -e 's/\t/\\t/g')

            # Write batch data as a JSON object
            echo "{\"batch_index\": $start_index," >> "$OUTPUT_FILE"
            echo "\"token_ids_candid\": \"$vec_argument\"," >> "$OUTPUT_FILE"
            echo "\"metadata_candid\": \"$escaped_metadata\"," >> "$OUTPUT_FILE"
            echo "\"owners_candid\": \"$escaped_owners\"}" >> "$OUTPUT_FILE"

            first_entry=false
        else
             echo "Warning: No token IDs extracted from non-empty response for batch $start_index."
             echo "Raw response: $tokens_response"
        fi

        # Move to the next batch start index
        start_index=$((start_index + batch_size))
    done

    # Close the JSON array and object properly
    echo "" >> "$OUTPUT_FILE" # Add newline for formatting
    echo "]}" >> "$OUTPUT_FILE"

    echo "Backup complete. Results are in $OUTPUT_FILE"
}

# Main execution
echo "Starting backup of entire token collection for Scion..."
process_tokens 0