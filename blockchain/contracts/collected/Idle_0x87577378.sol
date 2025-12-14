// Multi-file contract detected
// Full JSON structure (truncated to 500 chars):
{{
  "language": "Solidity",
  "sources": {
    "/home/bugman/Projects/idle-governance/contracts/ERC20Permit.sol": {
      "content": "// Permit pattern copied from BAL https://etherscan.io/address/0xba100000625a3754423978a60c9317c58a424e3d#code\npragma solidity 0.6.12;\n\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract ERC20Permit is ERC20 {\n  string public constant version = \"1\";\n  bytes32 public immutable DOMAIN_SEPARATOR;\n  // keccak256(\"Permit(address owner,a...

// TODO: Implement full multi-file extraction