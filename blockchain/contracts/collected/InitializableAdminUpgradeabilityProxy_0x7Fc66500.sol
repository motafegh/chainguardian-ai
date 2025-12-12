// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/interfaces/IERC20.sol": {
      "content": "// SPDX-License-Identifier: agpl-3.0\npragma solidity 0.6.10;\n\n/**\n * @dev Interface of the ERC20 standard as defined in the EIP.\n */\ninterface IERC20 {\n    /**\n     * @dev Returns the amount of tokens in existence.\n     */\n    function totalSupply() external view returns (uint256);\n\n    /**\n     * @dev Returns the amount of tokens owned by `account`.\n     */\n    function bala...

// TODO: Implement full multi-file extraction