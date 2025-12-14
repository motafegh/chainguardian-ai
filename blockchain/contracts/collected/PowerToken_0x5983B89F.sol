// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "lib/ttg/src/PowerToken.sol": {
      "content": "// SPDX-License-Identifier: GPL-3.0\n\npragma solidity 0.8.23;\n\nimport { ERC20Helper } from \"../lib/erc20-helper/src/ERC20Helper.sol\";\nimport { UIntMath } from \"../lib/common/src/libs/UIntMath.sol\";\n\nimport { PureEpochs } from \"./libs/PureEpochs.sol\";\n\nimport { IEpochBasedVoteToken } from \"./abstract/interfaces/IEpochBasedVoteToken.sol\";\n\nimport { EpochBasedInflationaryVoteToken...

// TODO: Implement full multi-file extraction