import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "./shared/BasicAccessControl.sol";
import "./Freezable.sol";

contract PEN is
    ERC20,
    ERC20Burnable,
    ERC20Permit,
    Freezable,
    BasicAccessControl
{
    bool public isTransferable = true;

    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10 ** 18;

    constructor() ERC20("Pentagon", "PEN") ERC20Permit("Pentagon") {
        _mint(msg.sender, MAX_SUPPLY);
        isTransferable = false;
    }

    function toggleIsTransferable() public onlyOwner {
        isTransferable = !isTransferable;
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override {
        super._beforeTokenTransfer(from, to, amount);
        require(
            moderators[_msgSender()] || isTransferable,
            "Cannot transfer to the provided address"
        );
        require(!isFrozen(from), "ERC20Freezable: from account is frozen");
        require(!isFrozen(to), "ERC20Freezable: to account is frozen");
    }

    function freeze(address _account) public onlyModerators {
        freezes[_account] = true;
        emit Frozen(_account);
    }

    function unfreeze(address _account) public onlyModerators {
        freezes[_account] = false;
        emit Unfrozen(_account);
    }
}
