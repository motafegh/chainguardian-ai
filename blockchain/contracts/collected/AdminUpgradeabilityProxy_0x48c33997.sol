// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/proxy/AdminUpgradeabilityProxy.sol": {
      "content": "// SPDX-License-Identifier: MIT\n\npragma solidity ^0.6.0;\n\nimport './UpgradeabilityProxy.sol';\n\n/**\n * @title AdminUpgradeabilityProxy\n * @dev This contract combines an upgradeability proxy with an authorization\n * mechanism for administrative tasks.\n * All external functions in this contract must be guarded by the\n * `ifAdmin` modifier. See ethereum/solidity#3864 for...

// TODO: Implement full multi-file extraction