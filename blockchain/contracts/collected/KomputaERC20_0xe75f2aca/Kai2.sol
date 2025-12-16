pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

contract KomputaERC20 is ERC20, ERC20Permit, Ownable {
    mapping(address => uint256) private _balances;

    uint256 private _totalSupply;

    bool public allowTransfer;
    mapping(address => bool) public authorized;

    constructor()
        ERC20("Komputai", "KAI")
        ERC20Permit("KAI")
        Ownable(msg.sender)
    {
        authorized[address(0)] = true;
        authorized[msg.sender] = true;

        _mint(msg.sender, 20000000 * 1 ether);
    }

    /**
     * To ensure that tokens are always transferable, this function is one-way.
     */
    function setAllowTransfer() external onlyOwner {
        allowTransfer = true;
    }

    function manageTransferAuthorization(address addr, bool _authorized)
        external
        onlyOwner
    {
        if (allowTransfer) {
            revert("Transfers are allowed, useless call");
        }

        authorized[addr] = _authorized;
    }

    function transfer(address to, uint256 value)
        public
        virtual
        override
        returns (bool)
    {
        if (!allowTransfer && !authorized[msg.sender]) {
            revert("Transfers are not allowed");
        }

        address owner = _msgSender();
        _transfer(owner, to, value);
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) public virtual override returns (bool) {
        if (!allowTransfer && !authorized[from]) {
            revert("Transfers are not allowed");
        }

        address spender = _msgSender();
        _spendAllowance(from, spender, value);
        _transfer(from, to, value);
        return true;
    }
}
