// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/Azuki.sol": {
      "content": "// SPDX-License-Identifier: MIT\n\npragma solidity ^0.8.0;\n\nimport \"@openzeppelin/contracts/access/Ownable.sol\";\nimport \"@openzeppelin/contracts/security/ReentrancyGuard.sol\";\nimport \"./ERC721A.sol\";\nimport \"@openzeppelin/contracts/utils/Strings.sol\";\n\ncontract Azuki is Ownable, ERC721A, ReentrancyGuard {\n  uint256 public immutable maxPerAddressDuringMint;\n  uint256 public immutable am...

// TODO: Implement full multi-file extraction