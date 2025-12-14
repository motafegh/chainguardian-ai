// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/CoolCats.sol": {
      "content": "// SPDX-License-Identifier: MIT\r\npragma solidity ^0.8.0;\r\n\r\nimport '@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol';\r\nimport '@openzeppelin/contracts/access/Ownable.sol';\r\n\r\ncontract CoolCats is ERC721Enumerable, Ownable {\r\n\r\n    using Strings for uint256;\r\n\r\n    string _baseTokenURI;\r\n    uint256 private _reserved = 100;\r\n    uint256 private _price = 0....

// TODO: Implement full multi-file extraction