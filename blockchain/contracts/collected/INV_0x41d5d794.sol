// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/token/INV.sol": {
      "content": "pragma solidity ^0.5.16;\n\npragma experimental ABIEncoderV2;\n\nimport \"./SafeMath.sol\";\n\ncontract INV {\n    /// @notice EIP-20 token name for this token\n    string public constant name = \"Inverse DAO\";\n\n    /// @notice EIP-20 token symbol for this token\n    string public constant symbol = \"INV\";\n\n    /// @notice EIP-20 token decimals for this token\n    uint8 public constant decima...

// TODO: Implement full multi-file extraction