#!/usr/bin/env python3

import os
import re

def parse_combined_output(file_path):
    tokens = []
    current_token = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Token ID:"):
                current_token['token_id'] = line.split(":")[1].strip()
            elif line.startswith("Owner:"):
                current_token['owner'] = line.split(":")[1].strip()
            elif line.startswith("Metadata:"):
                metadata = line.split(":", 1)[1].strip()
                description = re.search(r'Text = "([^"]*)"', metadata)
                current_token['description'] = description.group(1) if description else ""
            elif line == "---":
                tokens.append(current_token)
                current_token = {}
    
    return tokens

def generate_motoko_code(tokens):
    motoko_code = '''import ICRC7 "mo:icrc7-mo";
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
'''

    for token in tokens:
        motoko_code += f'      {{ token_id = {token["token_id"]}; owner = Principal.fromText("{token["owner"]}"); description = "{token["description"]}"; }},\n'

    motoko_code += '''    ];

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
'''
    return motoko_code

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    combined_output_file = os.path.join(script_dir, 'combined_output.txt')
    motoko_output_file = os.path.join(script_dir, 'nft_archive.mo')

    tokens = parse_combined_output(combined_output_file)
    motoko_code = generate_motoko_code(tokens)

    with open(motoko_output_file, 'w') as f:
        f.write(motoko_code)

    print(f"Motoko code has been generated and saved to {motoko_output_file}")

if __name__ == '__main__':
    main()
