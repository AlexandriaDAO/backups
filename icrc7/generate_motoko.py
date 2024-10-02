#!/usr/bin/env python3

import os
import re

def parse_token_ids(token_ids_line):
    match = re.search(r'Token IDs:\s*\(vec \{(.+)\}\)', token_ids_line)
    if match:
        token_ids_content = match.group(1)
        # Split on ';', strip whitespace
        token_ids = [token.strip() for token in token_ids_content.split(';') if token.strip()]
        return token_ids
    else:
        return []

def parse_owners(owners_lines):
    owners = []
    owner_pattern = re.compile(r'owner\s*=\s*principal\s*"([^"]+)"')
    for line in owners_lines:
        match = owner_pattern.search(line)
        if match:
            owners.append(match.group(1))
        else:
            owners.append(None)  # Handle null owners
    return owners

def parse_metadata(metadata_lines):
    metadata = []
    item = []
    in_item = False
    for line in metadata_lines:
        line = line.strip()
        if line.startswith('opt vec {'):
            in_item = True
            item = []
        elif line == '};':
            in_item = False
            if item:
                metadata_item = parse_metadata_item(item)
                metadata.append(metadata_item)
            else:
                metadata.append({})
        elif in_item:
            item.append(line)
        elif line == 'null;':
            metadata.append({})
    return metadata

def parse_metadata_item(item_lines):
    metadata_item = {}
    key = None
    value = None
    for line in item_lines:
        key_match = re.search(r'record\s*\{\s*"([^"]+)"', line)
        if key_match:
            key = key_match.group(1)
        value_match = re.search(r'variant\s*\{\s*Text\s*=\s*"([^"]*)"\s*\}', line)
        if value_match:
            value = value_match.group(1)
        if key and value is not None:
            metadata_item[key] = value
            key = None
            value = None
    return metadata_item

def parse_combined_output(file_path):
    tokens = []
    with open(file_path, 'r') as f:
        content = f.read()

    # Split the content into batches
    batches = content.strip().split('----------------------------------------')
    for batch in batches:
        if not batch.strip():
            continue
        lines = batch.strip().split('\n')
        # Extract Token IDs
        token_ids_line = next((line for line in lines if line.startswith('Token IDs:')), None)
        if token_ids_line:
            token_ids = parse_token_ids(token_ids_line)
        else:
            token_ids = []
        # Extract Owners
        try:
            owners_index = lines.index('Owners:')
            metadata_index = lines.index('Metadata:')
            owners_lines = lines[owners_index+1:metadata_index]
            owners = parse_owners(owners_lines)
            # Extract Metadata
            metadata_lines = lines[metadata_index+1:]
            metadata_list = parse_metadata(metadata_lines)
        except ValueError:
            # Handle missing sections
            owners = []
            metadata_list = []
        # Combine token IDs, owners, and metadata
        for idx, token_id in enumerate(token_ids):
            token_data = {
                'token_id': token_id,
                'owner': owners[idx] if idx < len(owners) else None,
                'metadata': metadata_list[idx] if idx < len(metadata_list) else {}
            }
            tokens.append(token_data)
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
        token_id = token['token_id']
        owner_principal = token['owner'] if token['owner'] else '2vxsx-fae'  # Default principal if none
        # For description, extract from metadata
        description = ''
        if token['metadata']:
            # Try to get 'description' key or any other key
            description = token['metadata'].get('description', '')
            if not description:
                description = next(iter(token['metadata'].values()), '')
        # Escape double quotes in description
        description = description.replace('"', '\\"')

        motoko_code += f'      {{ token_id = {token_id}; owner = Principal.fromText("{owner_principal}"); description = "{description}"; }},\n'

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
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    combined_output_file = os.path.join(script_dir, 'combined_output.txt')
    motoko_output_file = os.path.join(script_dir, 'initialize_nfts.mo')

    tokens = parse_combined_output(combined_output_file)
    motoko_code = generate_motoko_code(tokens)

    with open(motoko_output_file, 'w') as f:
        f.write(motoko_code)

    print(f"Motoko code has been generated and saved to {motoko_output_file}")

if __name__ == '__main__':
    main()
