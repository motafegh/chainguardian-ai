// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/token/Rail.sol": {
      "content": "// SPDX-License-Identifier: UNLICENSED\npragma solidity ^0.8.0;\npragma abicoder v2;\n\n// OpenZeppelin v4\nimport { Ownable } from  \"@openzeppelin/contracts/access/Ownable.sol\";\nimport { ERC20 } from \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\n/**\n * @title RailToken\n * @author Railgun Contributors\n * @notice ERC20 Railgun Governance Token\n */\n\ncontract RailToken is Ownable, ER...

// TODO: Implement full multi-file extraction