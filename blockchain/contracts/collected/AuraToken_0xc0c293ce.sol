// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "contracts/Aura.sol": {
      "content": "// SPDX-License-Identifier: MIT\npragma solidity 0.8.11;\n\nimport { ERC20 } from \"@openzeppelin/contracts-0.8/token/ERC20/ERC20.sol\";\nimport { AuraMath } from \"./AuraMath.sol\";\n\ninterface IStaker {\n    function operator() external view returns (address);\n}\n\n/**\n * @title   AuraToken\n * @notice  Basically an ERC20 with minting functionality operated by the \"operator\" of the VoterProxy (Bo...

// TODO: Implement full multi-file extraction