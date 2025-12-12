// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/SwapRouter.sol": {
      "content": "// SPDX-License-Identifier: GPL-2.0-or-later\npragma solidity =0.7.6;\npragma abicoder v2;\n\nimport '@uniswap/v3-core/contracts/libraries/SafeCast.sol';\nimport '@uniswap/v3-core/contracts/libraries/TickMath.sol';\nimport '@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol';\n\nimport './interfaces/ISwapRouter.sol';\nimport './base/PeripheryImmutableState.sol';\nimport './base/PeripheryVali...

// TODO: Implement full multi-file extraction