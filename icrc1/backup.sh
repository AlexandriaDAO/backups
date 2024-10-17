#!/bin/bash

set -e

# ALEX Canisterid
ALEX_CANISTER_ID="7hcrm-4iaaa-aaaak-akuka-cai"

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

# Pass the value to the Python script
python3 backup_tokenomics.py "$TOTAL_SUPPLY_ALEX"


ICP_SWAP_CANISTER_ID="5qx27-tyaaa-aaaal-qjafa-cai"
LEDGER_CANISTER_ID="ryjl3-tyaaa-aaaaa-aaaba-cai"

ICP_SWAP_BALANCE=$(dfx canister call "$LEDGER_CANISTER_ID" icrc1_balance_of "(record {owner = principal \"$ICP_SWAP_CANISTER_ID\";})" --network ic)

ICP_SWAP_BALANCE_NUMERIC=$(echo "$ICP_SWAP_BALANCE" | grep -oP '\(\K[0-9_]+(?=\s*:)' | tr -d '_')

if [ ${#ICP_SWAP_BALANCE_NUMERIC} -gt 8 ]; then
    ICP_SWAP_BALANCE=${ICP_SWAP_BALANCE_NUMERIC::-8}
else
    ICP_SWAP_BALANCE=$ICP_SWAP_BALANCE_NUMERIC
fi

python3 backup_stakes.py "$ICP_SWAP_BALANCE"
