// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/MapleTokenProxy.sol": {
      "content": "// SPDX-License-Identifier: BUSL-1.1\npragma solidity 0.8.18;\n\nimport { IMapleTokenInitializerLike, IGlobalsLike } from \"./interfaces/Interfaces.sol\";\nimport { IMapleTokenProxy }                         from \"./interfaces/IMapleTokenProxy.sol\";\n\ncontract MapleTokenProxy is IMapleTokenProxy {\n\n    bytes32 internal constant GLOBALS_SLOT        = bytes32(uint256(keccak256(\"eip1967.pr...

// TODO: Implement full multi-file extraction