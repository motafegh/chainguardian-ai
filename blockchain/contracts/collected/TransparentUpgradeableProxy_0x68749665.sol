// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/import.sol": {
      "content": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\nimport \"@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol\";\nimport \"@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol\";\nimport \"@openzeppelin/contracts/proxy/transparent/ProxyAdmin.sol\";\n\n// Kept for backwards compatibility with older versions of Hardhat and Truffle plugins.\ncontract AdminUpgradeability...

// TODO: Implement full multi-file extraction