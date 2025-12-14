// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {OFT} from "@layerzerolabs/oft-evm/contracts/OFT.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

contract YALA is OFT, ERC20Permit {
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 1e18;
    
    // Flag to identify the primary chain where initial minting occurs
    bool public immutable IS_PRIMARY_CHAIN;
    
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        address _lzEndpoint,
        address _delegate,
        address _receiver,
        address _admin,
        bool _isPrimaryChain
    ) OFT(_name, _symbol, _lzEndpoint, _delegate) 
      ERC20Permit(_name) {
        
        IS_PRIMARY_CHAIN = _isPrimaryChain;
        
        // Only mint initial supply on the primary chain
        if (_isPrimaryChain) {
            require(_initialSupply <= MAX_SUPPLY, "Initial supply exceeds max supply");
            _mint(_receiver, _initialSupply);
        }
        
        _transferOwnership(_admin);
    }

}