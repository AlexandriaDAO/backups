# ALEX Canisterid
ALEX_CANISTER_ID="7hcrm-4iaaa-aaaak-akuka-cai"
ICP_SWAP_CANISTER_ID="5qx27-tyaaa-aaaal-qjafa-cai"

dfx canister call $ALEX_CANISTER_ID icrc1_balance_of '(record {
    account = "ICP_SWAP_CANISTER_ID";
})'

# Now I need to get the record of transactions in and out of the ICP_SWAP_CANISTER_ID