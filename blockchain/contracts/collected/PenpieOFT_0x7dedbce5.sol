// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "@layerzerolabs/solidity-examples/contracts/interfaces/ILayerZeroEndpoint.sol": {
      "content": "// SPDX-License-Identifier: MIT\n\npragma solidity >=0.5.0;\n\nimport \"./ILayerZeroUserApplicationConfig.sol\";\n\ninterface ILayerZeroEndpoint is ILayerZeroUserApplicationConfig {\n    // @notice send a LayerZero message to the specified address at a LayerZero endpoint.\n    // @param _dstChainId - the destination chain identifier\n    // @para...

// TODO: Implement full multi-file extraction