// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "/home/hhofstadt/Dev/certus/wormhole/ethereum/contracts/bridge/TokenBridge.sol": {
      "content": "// contracts/Wormhole.sol\n// SPDX-License-Identifier: Apache 2\n\npragma solidity ^0.8.0;\n\nimport \"@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol\";\n\ncontract TokenBridge is ERC1967Proxy {\n    constructor (address implementation, bytes memory initData)\n    ERC1967Proxy(\n        implementation,\n        initData\n    )\n    {}\n}...

// TODO: Implement full multi-file extraction