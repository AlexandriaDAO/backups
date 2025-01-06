#!/bin/bash

: <<'COMMENT'

Requirements:

- Get the total staked

    dfx canister call 54fqz-5iaaa-aaaap-qkmqa-cai get_all_stakes --network ic
     # Output: 
     (
        vec {
            record {
            principal "2ljyd-77i5g-ix222-szy7a-ru4cu-ns4j7-kxc2z-oazam-igx3u-uwee6-yqe";
            record {
                time = 1_731_583_036_936_690_733 : nat64;
                reward_icp = 0 : nat64;
                amount = 6_360_495_920_000 : nat64;
            };
            };
        },
    )

    dfx canister call 54fqz-5iaaa-aaaap-qkmqa-cai get_total_archived_balance --network ic
    (0 : nat64) // Should be zero unless some transactions failed.

    dfx canister call 54fqz-5iaaa-aaaap-qkmqa-cai get_total_unclaimed_icp_reward --network ic
    # Output (distributed but not yet collected):
    (0 : nat64)

    dfx canister call ysy5f-2qaaa-aaaap-qkmmq-cai icrc1_total_supply --network ic
    (44_223_749_890_000 : nat)

    dfx canister call ryjl3-tyaaa-aaaaa-aaaba-cai icrc1_balance_of '(record { owner = principal "54fqz-5iaaa-aaaap-qkmqa-cai"; subaccount = null })' --network ic
    # (1_926_133_524 : nat)


There are 2 values I need to instantiate in the tokenomics canister: 
- Total LBRY Burned.
- Current Threshold Index.

dfx canister call 5abki-kiaaa-aaaap-qkmsa-cai get_total_LBRY_burn --network ic
# (37_965 : nat64)

dfx canister call 5abki-kiaaa-aaaap-qkmsa-cai get_current_threshold_index --network ic
# (1 : nat32)

COMMENT
