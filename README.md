- Check when there are over 1000 transactions and ensure there's no duplicates or missing blocks.
- One vulnerability would be if people burn LBRY on their own, and not through our UI, the total ALEX supply calculation and current mint block in our backups would be higher than the actual values. We might just be best off using the current total supply values.


### icp_swap

These are the values we back up for icp_swap:
- STAKES - We calculate this based on in and out flows to the staking canister.
- TOTAL_ALEX_STAKED - We calculate this from ALEX transactions.
- TOTAL_ICP_AVAILABLE - The current balance of the icp_swap canister wallet.

Things we don't do but should:
- TOTAL_UNCLAIMED_ICP_REWARD - We'll warn people this can be lost and they should collect rewards frequently, or set up an auto-claim function when the rewards get to a certain threshold.
- TOTAL_ARCHIVED_BALANCE - ???
- ARCHIVED_TRANSACTION_LOG - ???

Things we don't need to back up:
- STATE - Pending requests. We'll use this to check if there are any pending requests when we stop the canisters. (But will likely stop the frontend from working first and not use this).
- STAKEX
- LBRY_RATIO - Reinstantiated on redeploy.
- APY - Recalculated regularly.
- DISTRIBUTION_INTERVALS - This is hardcoded.

### tokenomics

All we need to back up is: 
- TOTAL_ALEX_MINTED
- TOTAL_LBRY_BURNED
- CURRENT_THRESHOLD

All we need to calculate these ar the total alex minted, which we get from icrc1_total_supply()

Then we map the maount that's been minted to the amount of LBRY that should have been burned.

And this brings us right back to the current threshold, which is the amount of LBRY that needs to be burned before the next threshold is reached.


#### ICRC7

Just litterally get all the NFTs and their data and back it up.