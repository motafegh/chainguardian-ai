// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/TokenDelegator.sol": {
      "content": "pragma solidity ^0.7.0;\npragma experimental ABIEncoderV2;\n\nimport { TokenDelegatorStorage, TokenEvents } from \"./TokenInterfaces.sol\";\n\ncontract InstaToken is TokenDelegatorStorage, TokenEvents {\n    constructor(\n        address account,\n        address implementation_,\n        uint initialSupply_,\n        uint mintingAllowedAfter_,\n        bool transferPaused_\n    ) {\n        r...

// TODO: Implement full multi-file extraction