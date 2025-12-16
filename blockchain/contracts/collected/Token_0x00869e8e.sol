// SPDX-License-Identifier: MIT

// Deployed On TWAP.DEV

pragma solidity ^0.8.20;

interface IToken {
    function creator() external view returns (address);
}

interface IWETH {
    function withdraw(uint256 amount) external;
}

interface IUniswapV3Factory {
    function getPool(
        address tokenA,
        address tokenB,
        uint24 fee
    ) external view returns (address);
}

interface ISwapRouter02 {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(
        ExactInputSingleParams calldata params
    ) external payable returns (uint256 amountOut);
}

interface INonfungiblePositionManager {
    struct MintParams {
        address token0;
        address token1;
        uint24 fee;
        int24 tickLower;
        int24 tickUpper;
        uint256 amount0Desired;
        uint256 amount1Desired;
        uint256 amount0Min;
        uint256 amount1Min;
        address recipient;
        uint256 deadline;
    }

    function factory() external view returns (address);

    function WETH9() external view returns (address);

    function positions(
        uint256 tokenId
    )
        external
        view
        returns (
            uint96 nonce,
            address operator,
            address token0,
            address token1,
            uint24 fee,
            int24 tickLower,
            int24 tickUpper,
            uint128 liquidity,
            uint256 feeGrowthInside0LastX128,
            uint256 feeGrowthInside1LastX128,
            uint128 tokensOwed0,
            uint128 tokensOwed1
        );

    function createAndInitializePoolIfNecessary(
        address token0,
        address token1,
        uint24 fee,
        uint160 sqrtPriceX96
    ) external returns (address pool);

    function mint(
        MintParams calldata params
    )
        external
        returns (
            uint256 tokenId,
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        );

    struct CollectParams {
        uint256 tokenId;
        address recipient;
        uint128 amount0Max;
        uint128 amount1Max;
    }

    function collect(
        CollectParams calldata params
    ) external payable returns (uint256 amount0, uint256 amount1);

    function getApproved(uint256 tokenId) external view returns (address);

    function isApprovedForAll(
        address owner,
        address operator
    ) external view returns (bool);

    function ownerOf(uint256 tokenId) external view returns (address);
}

contract Factory {
    event ERC20TokenCreated(address tokenAddress);
    event DeploymentStatusChanged(bool enabled);

    struct TokenInfo {
        address tokenAddress;
        string name;
        string symbol;
        address deployer;
        uint256 time;
        string metadata;
        uint256 marketCapInETH;
        uint24 feeTier;
    }

    mapping(uint256 => TokenInfo) public deployedTokens;
    uint256 public tokenCount = 0;
    address public platformController;

    bool private _isDeploymentActive = false;

    address public constant POSITION_MANAGER = 0xC36442b4a4522E871399CD717aBDD847Ab11FE88;
    address public constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant SWAP_ROUTER = 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45;

    uint24 public constant FEE_TIER_LOW = 500;
    uint24 public constant FEE_TIER_MEDIUM = 3000;
    uint24 public constant FEE_TIER_HIGH = 10000;

    uint256 private constant VIRTUAL_ETH = 1.5 ether;

    event TokenPurchased(
        address buyer,
        address tokenOut,
        uint256 ethSpent,
        uint256 tokensReceived
    );

    mapping(uint24 => int24) private tickSpacings;

    INonfungiblePositionManager private immutable positionManager;

    constructor() {
        platformController = msg.sender;
        
        positionManager = INonfungiblePositionManager(POSITION_MANAGER);
        
        IERC20(WETH).approve(POSITION_MANAGER, type(uint256).max);
        IERC20(WETH).approve(SWAP_ROUTER, type(uint256).max);

        tickSpacings[FEE_TIER_LOW] = 10;
        tickSpacings[FEE_TIER_MEDIUM] = 60;
        tickSpacings[FEE_TIER_HIGH] = 200;
    }

    receive() external payable {}

    function isDeploymentActive() external view returns (bool) {
        return _isDeploymentActive;
    }

    function deployToken(
        string memory _name,
        string memory _symbol,
        string memory _metadata,
        bytes32 salt,
        uint24 feeTier
    ) public payable {
        require(_isDeploymentActive, "Token deployment is currently disabled");
        require(bytes(_name).length > 0, "Token name cannot be empty");
        require(bytes(_symbol).length > 0, "Token symbol cannot be empty");
        require(
            feeTier == FEE_TIER_LOW ||
                feeTier == FEE_TIER_MEDIUM ||
                feeTier == FEE_TIER_HIGH,
            "Invalid fee tier. Must be 500, 3000, or 10000"
        );

        Token t = new Token{salt: salt}(
            _name,
            _symbol,
            msg.sender,
            address(this)
        );
        emit ERC20TokenCreated(address(t));

        address token_address = address(t);
        provideLiquidity(token_address, WETH, feeTier);

        if (msg.value > 0) {
            uint256 taxBps = getPenalty(msg.value);
            uint256 tax = (msg.value * taxBps) / 10000;
            uint256 amountAfterTax = msg.value - tax;

            ISwapRouter02(SWAP_ROUTER).exactInputSingle{value: amountAfterTax}(
                ISwapRouter02.ExactInputSingleParams({
                    tokenIn: WETH,
                    tokenOut: token_address,
                    fee: feeTier,
                    recipient: msg.sender,
                    amountIn: amountAfterTax,
                    amountOutMinimum: 0,
                    sqrtPriceLimitX96: 0
                })
            );
        }

        deployedTokens[tokenCount] = TokenInfo({
            tokenAddress: token_address,
            name: _name,
            symbol: _symbol,
            deployer: msg.sender,
            time: block.timestamp,
            metadata: _metadata,
            marketCapInETH: 0,
            feeTier: feeTier
        });
        tokenCount++;
    }

    function getTokenBytecode(
        string memory _name,
        string memory _symbol,
        address creator
    ) public view returns (bytes memory bytecode) {
        bytecode = abi.encodePacked(
            type(Token).creationCode,
            abi.encode(_name, _symbol, creator, address(this))
        );
    }

    function getPenalty(uint256 ethAmount) public pure returns (uint256) {
        if (ethAmount < 0.08 ether) return 0;
        if (ethAmount >= 0.5 ether) return 2000;

        uint256 delta = ethAmount - 0.08 ether;
        uint256 deltaSquared = (delta * delta) / 1 ether;
        uint256 penalty = (deltaSquared * 11338) / 1 ether;

        return penalty;
    }

    function getTokensByPage(
        uint256 page,
        uint256 order
    ) public view returns (TokenInfo[] memory) {
        uint256 itemsPerPage = 80;
        require(tokenCount > 0, "No tokens deployed");

        uint256 totalPages = (tokenCount + itemsPerPage - 1) / itemsPerPage;
        require(page < totalPages, "Page out of range");

        uint256 start;
        uint256 end;
        uint256 j = 0;

        if (order == 0) {
            start = tokenCount > (page + 1) * itemsPerPage
                ? tokenCount - (page + 1) * itemsPerPage
                : 0;
            end = tokenCount - page * itemsPerPage;
            if (end > tokenCount) end = tokenCount;
        } else {
            start = page * itemsPerPage;
            end = start + itemsPerPage;
            if (end > tokenCount) end = tokenCount;
        }

        TokenInfo[] memory tokens = new TokenInfo[](end - start);
        address weth = positionManager.WETH9();
        address factory = positionManager.factory();

        for (uint256 i = start; i < end; i++) {
            uint256 index = order == 0 ? end - 1 - (i - start) : i;
            TokenInfo memory info = deployedTokens[index];

            uint256 marketCap = 0;
            address pool = IUniswapV3Factory(factory).getPool(
                info.tokenAddress,
                weth,
                info.feeTier
            );
            if (pool != address(0)) {
                uint256 wethInPool = IERC20(weth).balanceOf(pool);
                uint256 tokenInPool = IERC20(info.tokenAddress).balanceOf(pool);
                uint256 totalSupply = IERC20(info.tokenAddress).totalSupply();

                if (tokenInPool > 0) {
                    marketCap =
                        ((wethInPool + VIRTUAL_ETH) * totalSupply) /
                        tokenInPool;
                }
            }

            tokens[j++] = TokenInfo({
                tokenAddress: info.tokenAddress,
                name: info.name,
                symbol: info.symbol,
                deployer: info.deployer,
                time: info.time,
                metadata: info.metadata,
                marketCapInETH: marketCap,
                feeTier: info.feeTier
            });
        }

        return tokens;
    }

    function getTokens(uint256 page) public view returns (TokenInfo[] memory) {
        require(tokenCount > 0, "No tokens deployed");

        uint256 itemsPerPage = 2000;
        uint256 totalPages = (tokenCount + itemsPerPage - 1) / itemsPerPage;
        require(page < totalPages, "Page out of range");

        uint256 start = tokenCount > (page + 1) * itemsPerPage
            ? tokenCount - (page + 1) * itemsPerPage
            : 0;
        uint256 end = tokenCount - page * itemsPerPage;
        if (end > tokenCount) end = tokenCount;

        TokenInfo[] memory tokens = new TokenInfo[](end - start);

        for (uint256 i = start; i < end; i++) {
            uint256 index = end - 1 - (i - start);
            TokenInfo memory info = deployedTokens[index];

            tokens[i - start] = TokenInfo({
                tokenAddress: info.tokenAddress,
                name: info.name,
                symbol: info.symbol,
                deployer: info.deployer,
                time: info.time,
                metadata: info.metadata,
                marketCapInETH: 0,
                feeTier: info.feeTier
            });
        }

        return tokens;
    }

    function getTokenByAddress(
        address tokenAddress
    ) public view returns (TokenInfo memory) {
        require(tokenAddress != address(0), "Invalid token address");
        require(tokenCount > 0, "No tokens deployed");

        address weth = positionManager.WETH9();
        address factory = positionManager.factory();

        for (uint256 i = 0; i < tokenCount; i++) {
            TokenInfo memory info = deployedTokens[i];
            if (info.tokenAddress == tokenAddress) {
                uint256 marketCap = 0;
                address pool = IUniswapV3Factory(factory).getPool(
                    info.tokenAddress,
                    weth,
                    info.feeTier
                );
                if (pool != address(0)) {
                    uint256 wethInPool = IERC20(weth).balanceOf(pool);
                    uint256 tokenInPool = IERC20(info.tokenAddress).balanceOf(
                        pool
                    );
                    uint256 totalSupply = IERC20(info.tokenAddress)
                        .totalSupply();

                    if (tokenInPool > 0) {
                        marketCap =
                            ((wethInPool + VIRTUAL_ETH) * totalSupply) /
                            tokenInPool;
                    }
                }

                return
                    TokenInfo({
                        tokenAddress: info.tokenAddress,
                        name: info.name,
                        symbol: info.symbol,
                        deployer: info.deployer,
                        time: info.time,
                        metadata: info.metadata,
                        marketCapInETH: marketCap,
                        feeTier: info.feeTier
                    });
            }
        }

        revert("Token not found");
    }

    function getTokenByMetadata(
        string memory metadata
    ) public view returns (TokenInfo memory) {
        require(bytes(metadata).length > 0, "Invalid metadata");
        require(tokenCount > 0, "No tokens deployed");

        address weth = positionManager.WETH9();
        address factory = positionManager.factory();

        for (uint256 i = 0; i < tokenCount; i++) {
            TokenInfo memory info = deployedTokens[i];
            if (keccak256(bytes(info.metadata)) == keccak256(bytes(metadata))) {
                uint256 marketCap = 0;
                address pool = IUniswapV3Factory(factory).getPool(
                    info.tokenAddress,
                    weth,
                    info.feeTier
                );
                if (pool != address(0)) {
                    uint256 wethInPool = IERC20(weth).balanceOf(pool);
                    uint256 tokenInPool = IERC20(info.tokenAddress).balanceOf(
                        pool
                    );
                    uint256 totalSupply = IERC20(info.tokenAddress)
                        .totalSupply();

                    if (tokenInPool > 0) {
                        marketCap =
                            ((wethInPool + VIRTUAL_ETH) * totalSupply) /
                            tokenInPool;
                    }
                }

                return
                    TokenInfo({
                        tokenAddress: info.tokenAddress,
                        name: info.name,
                        symbol: info.symbol,
                        deployer: info.deployer,
                        time: info.time,
                        metadata: info.metadata,
                        marketCapInETH: marketCap,
                        feeTier: info.feeTier
                    });
            }
        }

        revert("Token not found");
    }

    function rescueWETH() external {
        require(msg.sender == platformController, "Caller is not controller");
        uint256 wethBalance = IERC20(WETH).balanceOf(address(this));
        require(wethBalance > 0, "No WETH to withdraw");

        IWETH(WETH).withdraw(wethBalance);

        (bool success, ) = msg.sender.call{value: wethBalance}("");
        require(success, "ETH transfer failed");
    }

    function rescueETH() external {
        require(msg.sender == platformController, "Caller is not controller");

        uint256 ethBalance = address(this).balance;
        require(ethBalance > 0, "No ETH to withdraw");

        (bool success, ) = msg.sender.call{value: ethBalance}("");
        require(success, "ETH transfer failed");
    }

    function toggleDeployToken() external {
        require(msg.sender == platformController, "Caller is not controller");
        _isDeploymentActive = !_isDeploymentActive;
        emit DeploymentStatusChanged(_isDeploymentActive);
    }

    function getTickSpacing(uint24 feeTier) internal view returns (int24) {
        return tickSpacings[feeTier];
    }

    function provideLiquidity(
        address tokenA,
        address tokenB,
        uint24 feeTier
    ) internal {
        bool tokenAIsToken0 = tokenA < tokenB;
        address token0 = tokenAIsToken0 ? tokenA : tokenB;
        address token1 = tokenAIsToken0 ? tokenB : tokenA;

        if (token0 == WETH) {
            IERC20(token1).approve(POSITION_MANAGER, type(uint256).max);
        } else {
            IERC20(token0).approve(POSITION_MANAGER, type(uint256).max);
        }

        uint160 sqrtPriceX96 = tokenAIsToken0
            ? 3068365595550320841079178
            : 2045645379722529521098596513701367;

        int24 tickSpacing = getTickSpacing(feeTier);

        int24 tickLower;
        int24 tickUpper;

        if (tokenAIsToken0) {
            tickLower = -203000;
            tickUpper = 887200;
        } else {
            tickLower = -887200;
            tickUpper = 203000;
        }

        tickLower = (tickLower / tickSpacing) * tickSpacing;
        tickUpper = (tickUpper / tickSpacing) * tickSpacing;

        uint256 amount0Desired = tokenAIsToken0
            ? 1000000000000000000000000000
            : 0;
        uint256 amount1Desired = tokenAIsToken0
            ? 0
            : 1000000000000000000000000000;

        positionManager.createAndInitializePoolIfNecessary(
            token0,
            token1,
            feeTier,
            sqrtPriceX96
        );

        positionManager.mint(
            INonfungiblePositionManager.MintParams({
                token0: token0,
                token1: token1,
                fee: feeTier,
                tickLower: tickLower,
                tickUpper: tickUpper,
                amount0Desired: amount0Desired,
                amount1Desired: amount1Desired,
                amount0Min: 0,
                amount1Min: 0,
                recipient: address(this),
                deadline: block.timestamp
            })
        );
    }

    function collectFees(
        uint256 tokenId
    ) external returns (uint256 amount0, uint256 amount1) {
        (
            ,
            ,
            address token0Raw,
            address token1Raw,
            ,
            ,
            ,
            ,
            ,
            ,
            ,
        ) = positionManager.positions(tokenId);

        require(
            token0Raw != address(0) && token1Raw != address(0),
            "Invalid tokenId: position does not exist"
        );

        address createdToken;
        address wethToken;

        if (token0Raw == WETH) {
            createdToken = token1Raw;
            wethToken = token0Raw;
        } else if (token1Raw == WETH) {
            createdToken = token0Raw;
            wethToken = token1Raw;
        } else {
            revert("Neither token is WETH");
        }

        address creator = IToken(createdToken).creator();
        require(
            msg.sender == creator || msg.sender == platformController,
            "Not authorized"
        );

        uint256 beforeCreatedToken = IERC20(createdToken).balanceOf(
            address(this)
        );
        uint256 beforeWETH = IERC20(wethToken).balanceOf(address(this));

        INonfungiblePositionManager.CollectParams
            memory params = INonfungiblePositionManager.CollectParams({
                tokenId: tokenId,
                recipient: address(this),
                amount0Max: type(uint128).max,
                amount1Max: type(uint128).max
            });

        positionManager.collect(params);

        uint256 collectedCreatedToken = IERC20(createdToken).balanceOf(
            address(this)
        ) - beforeCreatedToken;
        uint256 collectedWETH = IERC20(wethToken).balanceOf(address(this)) -
            beforeWETH;

        if (collectedCreatedToken > 0) {
            IERC20(createdToken).transfer(
                address(0x000000000000000000000000000000000000dEaD),
                collectedCreatedToken
            );
        }

        if (collectedWETH > 0) {
            uint256 half = collectedWETH / 2;

            IWETH(wethToken).withdraw(half);

            (bool success, ) = payable(creator).call{value: half}("");
            require(success, "ETH transfer to creator failed");
        }

        if (token0Raw == WETH) {
            return (collectedWETH, collectedCreatedToken);
        } else {
            return (collectedCreatedToken, collectedWETH);
        }
    }
}

interface IERC20Errors {
    error ERC20InsufficientBalance(
        address sender,
        uint256 balance,
        uint256 needed
    );
    error ERC20InvalidSender(address sender);
    error ERC20InvalidReceiver(address receiver);
    error ERC20InsufficientAllowance(
        address spender,
        uint256 allowance,
        uint256 needed
    );
    error ERC20InvalidApprover(address approver);
    error ERC20InvalidSpender(address spender);
}

interface IERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );

    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function transfer(address to, uint256 value) external returns (bool);

    function allowance(
        address owner,
        address spender
    ) external view returns (uint256);

    function approve(address spender, uint256 value) external returns (bool);

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);
}

interface IERC20Metadata is IERC20 {
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);

    function decimals() external view returns (uint8);
}

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }

    function _contextSuffixLength() internal view virtual returns (uint256) {
        return 0;
    }
}

abstract contract ERC20 is Context, IERC20, IERC20Metadata, IERC20Errors {
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    uint256 private _totalSupply;
    string private _name;
    string private _symbol;

    constructor(string memory name_, string memory symbol_) {
        _name = name_;
        _symbol = symbol_;
    }

    function name() public view virtual returns (string memory) {
        return _name;
    }

    function symbol() public view virtual returns (string memory) {
        return _symbol;
    }

    function decimals() public view virtual returns (uint8) {
        return 18;
    }

    function totalSupply() public view virtual returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) public view virtual returns (uint256) {
        return _balances[account];
    }

    function transfer(address to, uint256 value) public virtual returns (bool) {
        address owner = _msgSender();
        _transfer(owner, to, value);
        return true;
    }

    function allowance(
        address owner,
        address spender
    ) public view virtual returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(
        address spender,
        uint256 value
    ) public virtual returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, value);
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) public virtual returns (bool) {
        address spender = _msgSender();
        _spendAllowance(from, spender, value);
        _transfer(from, to, value);
        return true;
    }

    function _transfer(address from, address to, uint256 value) internal {
        if (from == address(0)) {
            revert ERC20InvalidSender(address(0));
        }
        if (to == address(0)) {
            revert ERC20InvalidReceiver(address(0));
        }
        _update(from, to, value);
    }

    function _update(address from, address to, uint256 value) internal virtual {
        if (from == address(0)) {
            _totalSupply += value;
        } else {
            uint256 fromBalance = _balances[from];
            if (fromBalance < value) {
                revert ERC20InsufficientBalance(from, fromBalance, value);
            }
            unchecked {
                _balances[from] = fromBalance - value;
            }
        }

        if (to == address(0)) {
            unchecked {
                _totalSupply -= value;
            }
        } else {
            unchecked {
                _balances[to] += value;
            }
        }

        emit Transfer(from, to, value);
    }

    function _mint(address account, uint256 value) internal {
        if (account == address(0)) {
            revert ERC20InvalidReceiver(address(0));
        }
        _update(address(0), account, value);
    }

    function _burn(address account, uint256 value) internal {
        if (account == address(0)) {
            revert ERC20InvalidSender(address(0));
        }
        _update(account, address(0), value);
    }

    function _approve(address owner, address spender, uint256 value) internal {
        _approve(owner, spender, value, true);
    }

    function _approve(
        address owner,
        address spender,
        uint256 value,
        bool emitEvent
    ) internal virtual {
        if (owner == address(0)) {
            revert ERC20InvalidApprover(address(0));
        }
        if (spender == address(0)) {
            revert ERC20InvalidSpender(address(0));
        }
        _allowances[owner][spender] = value;
        if (emitEvent) {
            emit Approval(owner, spender, value);
        }
    }

    function _spendAllowance(
        address owner,
        address spender,
        uint256 value
    ) internal virtual {
        uint256 currentAllowance = allowance(owner, spender);
        if (currentAllowance < type(uint256).max) {
            if (currentAllowance < value) {
                revert ERC20InsufficientAllowance(
                    spender,
                    currentAllowance,
                    value
                );
            }
            unchecked {
                _approve(owner, spender, currentAllowance - value, false);
            }
        }
    }
}

abstract contract ERC20Burnable is Context, ERC20 {
    function burn(uint256 value) public virtual {
        _burn(_msgSender(), value);
    }

    function burnFrom(address account, uint256 value) public virtual {
        _spendAllowance(account, _msgSender(), value);
        _burn(account, value);
    }
}

contract Token is ERC20, ERC20Burnable {
    address public platform;
    address public creator;
    uint256 private launchTime;
    uint256 private maxTxAmount;
    uint256 private constant INITIAL_TIMELOCK = 60;
    uint256 private constant WALLET_CAP_PERCENT = 2;

    constructor(
        string memory _name,
        string memory _symbol,
        address _creator,
        address _platform
    ) ERC20(_name, _symbol) {
        uint256 totalTokens = 1000000000 * 10 ** decimals();

        platform = _platform;
        creator = _creator;
        launchTime = block.timestamp;
        maxTxAmount = (totalTokens * WALLET_CAP_PERCENT) / 100;

        _mint(_platform, totalTokens);
    }

    function _update(
        address from,
        address to,
        uint256 value
    ) internal override {
        if (
            from == address(0) ||
            to == address(0) ||
            to == creator ||
            to == platform ||
            from == platform
        ) {
            super._update(from, to, value);
            return;
        }

        uint256 currentTime = block.timestamp;

        if (currentTime == launchTime) revert("No buys at launch block");

        if (
            currentTime < launchTime + INITIAL_TIMELOCK &&
            balanceOf(to) + value > maxTxAmount
        ) {
            revert("Max 2% wallet limit during launch");
        }

        super._update(from, to, value);
    }

    function isLaunchPeriodActive() public view returns (bool) {
        return block.timestamp < launchTime + INITIAL_TIMELOCK;
    }
}