// File: contracts\Freezable\Freezable.sol

pragma solidity ^0.8.2;

//import "@openzeppelin/contracts/utils/Context.sol";

/*
 ** usage:
 **   require(!isFrozen(_account), "Freezable: frozen");
 ** or
 **   modifier: whenAccountNotFrozen(address _account)
 ** or
 **   require(!freezes[_from], "From account is locked.");
 */
//abstract contract Freezable is Context {
abstract contract Freezable {
    event Frozen(address account);
    event Unfrozen(address account);
    mapping(address => bool) internal freezes;

    function isFrozen(address _account) public view virtual returns (bool) {
        return freezes[_account];
    }

    modifier whenAccountNotFrozen(address _account) {
        require(!isFrozen(_account), "Freezable: frozen");
        _;
    }

    modifier whenAccountFrozen(address _account) {
        require(isFrozen(_account), "Freezable: not frozen");
        _;
    }
}
