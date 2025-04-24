#!/usr/bin/env python3

import os
import re
import json

# Function to extract the last Candid vec/opt vec string from shell output
def extract_candid_from_output(output_str):
    # Find the start index of the last potential Candid result
    last_vec_start = output_str.rfind('(vec {')
    last_opt_vec_start = output_str.rfind('(opt vec {')
    
    start_pos = -1
    if last_vec_start != -1 and last_opt_vec_start != -1:
        start_pos = max(last_vec_start, last_opt_vec_start)
    elif last_vec_start != -1:
        start_pos = last_vec_start
    elif last_opt_vec_start != -1:
        start_pos = last_opt_vec_start
        
    if start_pos != -1:
        # Look for the matching closing parenthesis from this start position
        open_paren_count = 0
        end_pos = -1
        # Iterate from the character position where '(vec {' or '(opt vec {' starts
        for i in range(start_pos, len(output_str)):
            if output_str[i] == '(':
                open_paren_count += 1
            elif output_str[i] == ')':
                open_paren_count -= 1
                if open_paren_count == 0:
                    end_pos = i
                    break # Found the matching closing parenthesis
        
        if end_pos != -1:
             # Return the substring from the start '(' to the matching ')'
             return output_str[start_pos : end_pos + 1].strip() # Strip leading/trailing whitespace
             
    # Fallback or error case
    print(f"  Warning: Could not extract Candid structure from output snippet: {output_str[-200:]}") # Print last part of string for context
    return "" # Return empty string if not found

def parse_json_output(file_path):
    tokens = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Handle potentially problematic JSON format
            content = content.replace('\\tokens\\:', '"tokens":')
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Problematic content near position {e.pos}")
                return []
            
            # Process each batch of token data
            for batch in data.get('tokens', []):
                # Extract token IDs
                token_ids_str = batch.get('token_ids_candid', '')
                token_ids = re.findall(r'([0-9_]+)', token_ids_str)
                
                # Extract owners
                owners_str = batch.get('owners_candid', '')
                owners = re.findall(r'principal\s*"([^"]+)"', owners_str)
                
                # Extract descriptions
                metadata_str = batch.get('metadata_candid', '')
                descriptions = re.findall(r'Text\s*=\s*"([^"]*)"', metadata_str)
                
                # Combine the data
                if len(token_ids) == len(owners) == len(descriptions):
                    for i in range(len(token_ids)):
                        tokens.append({
                            'token_id': token_ids[i],
                            'owner': owners[i],
                            'description': descriptions[i]
                        })
                else:
                    print(f"Warning: Mismatch in data lengths for batch {batch.get('batch_index', 'N/A')}.")
                    print(f"  Token IDs: {len(token_ids)}, Owners: {len(owners)}, Descriptions: {len(descriptions)}")
                    
                    # Try to salvage what we can with a more tolerant approach
                    max_length = max(len(token_ids), len(owners), len(descriptions))
                    for i in range(max_length):
                        if i < len(token_ids) and i < len(owners) and i < len(descriptions):
                            tokens.append({
                                'token_id': token_ids[i],
                                'owner': owners[i],
                                'description': descriptions[i]
                            })
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    
    return tokens

def format_number_with_underscores(number_str):
    """Format a number string with underscores for better readability in Motoko"""
    # Remove any existing underscores
    clean_number = number_str.replace('_', '')
    
    # Convert to int and format with underscores for thousand separators
    try:
        num = int(clean_number)
        # Use the built-in formatting for readability
        return format(num, '_')
    except ValueError:
        # If conversion fails, return the original
        return number_str

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
        # Format the token_id with underscores for readability
        formatted_token_id = format_number_with_underscores(token["token_id"])
        # Escape any double quotes in the description
        escaped_description = token["description"].replace('"', '\\"')
        motoko_code += f'      {{ token_id = {formatted_token_id}; owner = Principal.fromText("{token["owner"]}"); description = "{escaped_description}"; }},\n'

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
    json_input_file = os.path.join(script_dir, 'nft_data.json')
    motoko_output_file = os.path.join(script_dir, 'nft_archive.mo')

    print(f"Parsing NFT data from {json_input_file}...")
    tokens = parse_json_output(json_input_file)
    print(f"Successfully parsed {len(tokens)} tokens")
    
    print("Generating Motoko code...")
    motoko_code = generate_motoko_code(tokens)

    with open(motoko_output_file, 'w') as f:
        f.write(motoko_code)

    print(f"Motoko code has been generated and saved to {motoko_output_file}")

if __name__ == '__main__':
    main()













































# #!/usr/bin/env python3

# import os
# import re

# def parse_combined_output(file_path):
#     tokens = []
#     current_token = {}
    
#     with open(file_path, 'r') as f:
#         for line in f:
#             line = line.strip()
#             if line.startswith("Token ID:"):
#                 current_token['token_id'] = line.split(":")[1].strip()
#             elif line.startswith("Owner:"):
#                 current_token['owner'] = line.split(":")[1].strip()
#             elif line.startswith("Metadata:"):
#                 metadata = line.split(":", 1)[1].strip()
#                 description = re.search(r'Text = "([^"]*)"', metadata)
#                 current_token['description'] = description.group(1) if description else ""
#             elif line == "---":
#                 tokens.append(current_token)
#                 current_token = {}
    
#     return tokens

# def generate_motoko_code(tokens):
#     motoko_code = '''import ICRC7 "mo:icrc7-mo";
# import Principal "mo:base/Principal";
# import D "mo:base/Debug";
# import Array "mo:base/Array";

# module {
#   // Define a type for the variable parts of each NFT
#   type NFTData = {
#     token_id: Nat;
#     owner: Principal;
#     description: Text;
#   };

#   public func initialize_nfts(icrc7: ICRC7.ICRC7, caller: Principal) : async () {
#     let base_nft : ICRC7.SetNFTItemRequest = {
#       created_at_time = null;
#       memo = null;
#       metadata = #Text(""); // Use an empty string as a placeholder
#       override = false;
#       owner = null; // This will be overwritten
#       token_id = 0; // This will be overwritten
#     };

#     // Define the variable data for each NFT
#     let nft_data : [NFTData] = [
# '''

#     for token in tokens:
#         motoko_code += f'      {{ token_id = {token["token_id"]}; owner = Principal.fromText("{token["owner"]}"); description = "{token["description"]}"; }},\n'

#     motoko_code += '''    ];

#     let initial_nfts = Array.map<NFTData, ICRC7.SetNFTItemRequest>(
#       nft_data,
#       func (data: NFTData) : ICRC7.SetNFTItemRequest {
#         {
#           base_nft with
#           token_id = data.token_id;
#           owner = ?{owner = data.owner; subaccount = null;};
#           metadata = #Map([("description", #Text(data.description))]);
#         }
#       }
#     );

#     let set_nft_request : ICRC7.SetNFTRequest = initial_nfts;

#     switch(icrc7.set_nfts<system>(caller, set_nft_request, true)){
#       case(#ok(val)) D.print("Successfully initialized NFTs: " # debug_show(val));
#       case(#err(err)) D.trap("Failed to initialize NFTs: " # err);
#     };
#   };
# }
# '''
#     return motoko_code

# def main():
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     combined_output_file = os.path.join(script_dir, 'combined_output.txt')
#     motoko_output_file = os.path.join(script_dir, 'nft_archive.mo')

#     tokens = parse_combined_output(combined_output_file)
#     motoko_code = generate_motoko_code(tokens)

#     with open(motoko_output_file, 'w') as f:
#         f.write(motoko_code)

#     print(f"Motoko code has been generated and saved to {motoko_output_file}")

# if __name__ == '__main__':
#     main()