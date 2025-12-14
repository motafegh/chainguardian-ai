// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/UniswapV3Pool.sol": {
      "content": "// SPDX-License-Identifier: BUSL-1.1\npragma solidity =0.7.6;\n\nimport './interfaces/IUniswapV3Pool.sol';\n\nimport './NoDelegateCall.sol';\n\nimport './libraries/LowGasSafeMath.sol';\nimport './libraries/SafeCast.sol';\nimport './libraries/Tick.sol';\nimport './libraries/TickBitmap.sol';\nimport './libraries/Position.sol';\nimport './libraries/Oracle.sol';\n\nimport './libraries/FullMath.sol'...

// TODO: Implement full multi-file extraction