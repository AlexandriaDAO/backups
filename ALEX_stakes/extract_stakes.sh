#!/bin/bash

# ALEX Canisterid
ALEX_CANISTER_ID="7hcrm-4iaaa-aaaak-akuka-cai"
ICP_SWAP_CANISTER_ID="5qx27-tyaaa-aaaal-qjafa-cai"

# Set start and length for icrc3_get_blocks
START=0
LENGTH=1000

# Save the output to a file with start and length arguments
dfx canister call "$ALEX_CANISTER_ID" icrc3_get_blocks '(vec { record { start = '$START'; length = '$LENGTH' } })' --network ic --output json | sed 's/^(//;s/)$//' | jq '.' > blocks.json

