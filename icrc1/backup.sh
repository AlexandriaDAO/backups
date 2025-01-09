#!/bin/bash

set -e

# ALEX Canisterid
ALEX_CANISTER_ID="ysy5f-2qaaa-aaaap-qkmmq-cai"
ICP_SWAP_CANISTER_ID="54fqz-5iaaa-aaaap-qkmqa-cai"
LEDGER_CANISTER_ID="ryjl3-tyaaa-aaaaa-aaaba-cai"

# Get the total supply of ALEX and save it to a variable
ALEX_TOTAL_SUPPLY=$(dfx canister call "$ALEX_CANISTER_ID" icrc1_total_supply --network ic)

# Extract the numeric value using grep and sed
ALEX_TOTAL_SUPPLY_NUMERIC=$(echo "$ALEX_TOTAL_SUPPLY" | grep -oP '\(\K[0-9_]+(?=\s*:)' | tr -d '_')

# Remove the last 8 digits (decimal places) if the string is long enough
if [ ${#ALEX_TOTAL_SUPPLY_NUMERIC} -gt 8 ]; then
    TOTAL_SUPPLY_ALEX=${ALEX_TOTAL_SUPPLY_NUMERIC::-8}
else
    TOTAL_SUPPLY_ALEX=$ALEX_TOTAL_SUPPLY_NUMERIC
fi

# Get ICP balance
ICP_SWAP_BALANCE=$(dfx canister call "$LEDGER_CANISTER_ID" icrc1_balance_of "(record {owner = principal \"$ICP_SWAP_CANISTER_ID\";})" --network ic)

ICP_SWAP_BALANCE_NUMERIC=$(echo "$ICP_SWAP_BALANCE" | grep -oP '\(\K[0-9_]+(?=\s*:)' | tr -d '_')

if [ ${#ICP_SWAP_BALANCE_NUMERIC} -gt 8 ]; then
    ICP_SWAP_BALANCE=${ICP_SWAP_BALANCE_NUMERIC::-8}
else
    ICP_SWAP_BALANCE=$ICP_SWAP_BALANCE_NUMERIC
fi

# Get all stakes
STAKES_DATA=$(dfx canister call "$ICP_SWAP_CANISTER_ID" get_all_stakes --network ic)

# Save stakes data to a temporary file in the current directory
TEMP_FILE="./temp_stakes.txt"
echo "$STAKES_DATA" > "$TEMP_FILE"

# Call the Python script with the stakes file
python3 backup.py "$TOTAL_SUPPLY_ALEX" "$ICP_SWAP_BALANCE" "$TEMP_FILE"

# Clean up temporary file
rm "$TEMP_FILE"
