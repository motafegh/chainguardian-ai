// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "src/CFG.sol": {
      "content": "// SPDX-License-Identifier: GPL-2.0-or-later\npragma solidity 0.8.28;\n\nimport {DelegationToken} from \"src/DelegationToken.sol\";\nimport {ICFG} from \"src/interfaces/ICFG.sol\";\n\n/// @title  Centrifuge Token\ncontract CFG is DelegationToken, ICFG {\n    constructor(address ward) DelegationToken(18) {\n        file(\"name\", \"Centrifuge\");\n        file(\"symbol\", \"CFG\");\n        rely(ward);\n    }\n...

// TODO: Implement full multi-file extraction