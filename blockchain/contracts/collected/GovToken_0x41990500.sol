// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "src/dao/GovToken.sol": {
      "content": "// SPDX-License-Identifier: MIT\npragma solidity 0.8.28;\n\nimport { Ownable } from \"@openzeppelin/contracts/access/Ownable.sol\";\nimport { OFT } from \"@layerzerolabs/oft-evm/contracts/OFT.sol\";\n\ncontract GovToken is OFT {\n    uint256 public immutable INITIAL_SUPPLY;\n    uint256 public globalSupply;\n    bool public minterFinalized;\n    address public minter;\n\n    event FinalizeMinter();\n ...

// TODO: Implement full multi-file extraction