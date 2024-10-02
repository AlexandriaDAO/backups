import ICRC7 "mo:icrc7-mo";
import Principal "mo:base/Principal";
import D "mo:base/Debug";
import Array "mo:base/Array";

module {
  // Define a type for the variable parts of each NFT
  type NFTData = {
    token_id: Nat;
    owner: Principal;
    description: Text;
  };

  public func initialize_nfts(icrc7: ICRC7.ICRC7, caller: Principal) : async () {
    let base_nft : ICRC7.SetNFTItemRequest = {
      created_at_time = null;
      memo = null;
      metadata = #Text(""); // Use an empty string as a placeholder
      override = false;
      owner = null; // This will be overwritten
      token_id = 0; // This will be overwritten
    };

    // Define the variable data for each NFT
    let nft_data : [NFTData] = [
      { token_id = 0; owner = Principal.fromText("forhl-tiaaa-aaaak-qc7ga-cai"); description = "-LdjHXYDaKmlyRTxYifARQ0MB5MsMOEqbgz3UHhiUmQ"; },
      { token_id = 1; owner = Principal.fromText("forhl-tiaaa-aaaak-qc7ga-cai"); description = "-eu2OTDgao-_JiGTLmNFHrltXLxPJWDHe7Cjmr0NJWI"; },
      { token_id = 2; owner = Principal.fromText("3dJqKLtezxKbQUBJy-wIQPugHSP6_CWjBmCO2mT3rkc"); description = "asdf"; },
    ];

    let initial_nfts = Array.map<NFTData, ICRC7.SetNFTItemRequest>(
      nft_data,
      func (data: NFTData) : ICRC7.SetNFTItemRequest {
        {
          base_nft with
          token_id = data.token_id;
          owner = ?{owner = data.owner; subaccount = null;};
          metadata = #Map([("description", #Text(data.description))]);
        }
      }
    );

    let set_nft_request : ICRC7.SetNFTRequest = initial_nfts;

    switch(icrc7.set_nfts<system>(caller, set_nft_request, true)){
      case(#ok(val)) D.print("Successfully initialized NFTs: " # debug_show(val));
      case(#err(err)) D.trap("Failed to initialize NFTs: " # err);
    };
  };
}