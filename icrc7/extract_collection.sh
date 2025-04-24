#!/bin/bash

NETWORK="ic"
CANISTER_ID="53ewn-qqaaa-aaaap-qkmqq-cai"
# Reduce batch size to avoid potential command length issues / parser limits
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

# Initialize output file
echo "{" > "$OUTPUT_FILE"
echo "\"tokens\": [" >> "$OUTPUT_FILE"

first_entry=true
start_index=0

while true; do
    echo "Fetching batch starting at $start_index (size $BATCH_SIZE)..."
    
    # Get batch of token IDs
    tokens_response=$(run_dfx "icrc7_tokens" "(opt $start_index, opt $BATCH_SIZE)")

    # Check for errors in fetching token IDs
    if echo "$tokens_response" | grep -q "Error:"; then
        echo "Error fetching token IDs batch starting at $start_index."
        echo "Response: $tokens_response"
        # Decide how to handle: exit, skip, retry? For now, exit.
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
    # Get content inside vec { ... }
    tokens_content=$(echo "$tokens_response" | sed -n 's/.*vec {\(.*\)}.*/\1/p')
    # Extract numbers (digits and underscores)
    token_ids_list=$(echo "$tokens_content" | grep -oE '[0-9_]+')
    
    # If we got token IDs, get their metadata and owners in batch
    if [ -n "$token_ids_list" ]; then
        # Format them into a semicolon-separated string for Candid vec
        semicolon_separated_ids=$(echo "$token_ids_list" | paste -sd ';')
        vec_argument="(vec {$semicolon_separated_ids})"
        
        # Get metadata and ownership in single batch calls
        echo "Fetching metadata for ${#token_ids_list[@]} tokens..."
        metadata_response=$(run_dfx "icrc7_token_metadata" "$vec_argument")
        echo "Fetching owners for ${#token_ids_list[@]} tokens..."
        owner_response=$(run_dfx "icrc7_owner_of" "$vec_argument")
        
        # Check for errors in metadata/owner calls
        if echo "$metadata_response" | grep -q "Error:" || echo "$owner_response" | grep -q "Error:"; then
            echo "Error fetching metadata or owners for batch starting at $start_index."
            echo "Token IDs vec: $vec_argument"
            echo "Metadata Response: $metadata_response"
            echo "Owner Response: $owner_response"
            # Skip this batch
            echo "Skipping this batch due to error."
            start_index=$((start_index + BATCH_SIZE))
            continue 
        fi

        # Process and save the data
        if [ "$first_entry" = false ]; then
            # Add comma separator before the next entry
            echo "," >> "$OUTPUT_FILE"
        fi
        
        # Save the raw responses, properly escaped for JSON
        # Escape backslashes, double quotes, and control characters (like newlines)
        escaped_metadata=$(echo "$metadata_response" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g' -e 's/\t/\\t/g')
        escaped_owners=$(echo "$owner_response" | sed -e ':a' -e 'N' -e '$!ba' -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\n/\\n/g' -e 's/\t/\\t/g')
        # vec_argument should be safe as it only contains numbers, underscores, ';', '{', '}', '(', ')', 'vec', ' '

        echo "{\"batch_index\": $start_index," >> "$OUTPUT_FILE"
        echo "\"token_ids_candid\": \"$vec_argument\"," >> "$OUTPUT_FILE"
        echo "\"metadata_candid\": \"$escaped_metadata\"," >> "$OUTPUT_FILE"
        echo "\"owners_candid\": \"$escaped_owners\"}" >> "$OUTPUT_FILE" # No trailing comma here
        
        first_entry=false
    else
         # This case means the icrc7_tokens response was not '(vec {})' but we couldn't extract IDs.
         echo "Warning: No token IDs extracted from non-empty response for batch $start_index."
         echo "Raw response: $tokens_response"
         # Consider logging or handling this case more robustly if it occurs.
    fi
    
    # Move to the next batch start index
    # We need the actual count of tokens returned in the last batch to determine the next start index accurately if the canister doesn't return exactly BATCH_SIZE items near the end.
    # However, the icrc7_tokens standard doesn't explicitly return the count, just the tokens.
    # Assuming the standard pagination works by just requesting the next offset.
    # If the last batch returned fewer than BATCH_SIZE items, the next call with offset start_index + BATCH_SIZE should return vec {} anyway.
    start_index=$((start_index + BATCH_SIZE))

done

# Close the JSON array and object properly
echo "" >> "$OUTPUT_FILE" # Add a newline for cleaner formatting before closing chars
echo "]}" >> "$OUTPUT_FILE"

echo "Script finished. Data saved in $OUTPUT_FILE"