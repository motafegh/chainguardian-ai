// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/tokens/GearToken.sol": {
      "content": "// SPDX-License-Identifier: BSD-3-Clause\npragma solidity ^0.7.4;\npragma experimental ABIEncoderV2;\nimport {SafeMath} from \"@openzeppelin/contracts/math/SafeMath.sol\";\n\n/// @dev Governance Gearbox token\n/// based on https://github.com/Uniswap/governance/blob/master/contracts/Uni.sol\ncontract GearToken {\n    /// @notice EIP-20 token name for this token\n    string public constant nam...

// TODO: Implement full multi-file extraction