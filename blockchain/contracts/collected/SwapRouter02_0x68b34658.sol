// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/SwapRouter02.sol": {
      "content": "// SPDX-License-Identifier: GPL-2.0-or-later\npragma solidity =0.7.6;\npragma abicoder v2;\n\nimport '@uniswap/v3-periphery/contracts/base/SelfPermit.sol';\nimport '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol';\n\nimport './interfaces/ISwapRouter02.sol';\nimport './V2SwapRouter.sol';\nimport './V3SwapRouter.sol';\nimport './base/ApproveAndCall.sol';\nimport './base/Multicall...

// TODO: Implement full multi-file extraction