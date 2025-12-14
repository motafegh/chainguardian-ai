// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/governance/Eul.sol": {
      "content": "// SPDX-License-Identifier: MIT\n\npragma solidity ^0.8.0;\n\nimport \"@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol\";\nimport \"@openzeppelin/contracts/access/AccessControl.sol\";\n\ncontract Eul is ERC20Votes, AccessControl {\n    /// @notice The role assigned to users who can call admin/restricted functions\n    bytes32 public constant ADMIN_ROLE = keccak256(\"ADMIN_ROLE\")...

// TODO: Implement full multi-file extraction