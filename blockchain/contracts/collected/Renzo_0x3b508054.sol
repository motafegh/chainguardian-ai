// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contract-40735d62d1.sol": {
      "content": "// SPDX-License-Identifier: MIT\n// Compatible with OpenZeppelin Contracts ^5.0.0\npragma solidity ^0.8.20;\n\nimport \"@openzeppelin/contracts@5.0.2/token/ERC20/ERC20.sol\";\nimport \"@openzeppelin/contracts@5.0.2/token/ERC20/extensions/ERC20Permit.sol\";\nimport \"@openzeppelin/contracts@5.0.2/token/ERC20/extensions/ERC20Votes.sol\";\n\ncontract Renzo is ERC20, ERC20Permit, ERC20Votes {\n    cons...

// TODO: Implement full multi-file extraction