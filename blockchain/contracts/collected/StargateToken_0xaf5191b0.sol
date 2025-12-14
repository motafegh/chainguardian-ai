// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/StargateToken.sol": {
      "content": "// SPDX-License-Identifier: BUSL-1.1\n\npragma solidity 0.7.6;\n\nimport \"./OmnichainFungibleToken.sol\";\n\ncontract StargateToken is OmnichainFungibleToken {\n    constructor(\n        string memory _name,\n        string memory _symbol,\n        address _endpoint,\n        uint16 _mainEndpointId,\n        uint256 _initialSupplyOnMainEndpoint\n    ) OmnichainFungibleToken(_name, _symbol, _en...

// TODO: Implement full multi-file extraction