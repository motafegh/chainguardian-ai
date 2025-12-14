// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/adapters/CommonAdapter.sol": {
      "content": "pragma solidity ^0.6.0;\r\n\r\nimport \"@openzeppelin/contracts/token/ERC20/IERC20.sol\";\r\nimport \"@openzeppelin/contracts/token/ERC20/SafeERC20.sol\";\r\nimport \"@openzeppelin/contracts/utils/Address.sol\";\r\n\r\nimport \"../Constants.sol\";\r\n\r\ncontract CommonAdapter {\r\n    using SafeERC20 for IERC20;\r\n    using Address for address;\r\n    using Address for address payabl...

// TODO: Implement full multi-file extraction