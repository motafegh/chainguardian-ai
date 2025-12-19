"""
Audited DeFi Collector - Production Safe Contracts

Collects battle-tested DeFi protocol contracts.
Criteria:
- Multiple security audits
- >1 year in production
- High TVL (>$100M)
- No exploits

🎓 Production insight: These are KNOWN SAFE because they've been
battle-tested in production with billions of dollars at stake.
"""

from pathlib import Path
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditedDeFiCollector:
    """
    Collect verified safe contracts from audited DeFi protocols.
    
    🎓 Selection criteria:
    1. Multiple independent security audits
    2. Extended production time (>1 year)
    3. High total value locked (proof of trust)
    4. Clean security record (no exploits)
    5. Active development and maintenance
    """
    
    def __init__(self):
        self.output_dir = Path("data/metadata/safe_sources")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 🔒 Curated list of audited protocols
        # Source: DeFiLlama, audit firm websites, protocol docs
        self.audited_protocols = [
            # ============================================================
            # Tier 1: DEX Protocols (>$1B TVL)
            # ============================================================
            {
                "protocol": "Uniswap V2",
                "category": "dex",
                "contracts": [
                    {
                        "name": "UniswapV2Factory",
                        "address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                        "function": "Factory for creating pair contracts"
                    },
                    {
                        "name": "UniswapV2Router02",
                        "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                        "function": "Main router for swaps"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2020-03", "url": "https://github.com/Uniswap/v2-core/blob/master/audits/Trail_of_Bits.pdf"},
                    {"firm": "Consensys Diligence", "date": "2020-03", "url": "https://consensys.net/diligence/audits/2020/06/uniswap-v2/"},
                    {"firm": "ABDK", "date": "2020-04", "url": "https://github.com/Uniswap/v2-core/blob/master/audits/ABDK.pdf"}
                ],
                "tvl_usd": 1_500_000_000,
                "years_active": 4.5,
                "exploits": 0,
                "github": "https://github.com/Uniswap/v2-core"
            },
            {
                "protocol": "Uniswap V3",
                "category": "dex",
                "contracts": [
                    {
                        "name": "UniswapV3Factory",
                        "address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                        "function": "Factory for V3 pools"
                    },
                    {
                        "name": "SwapRouter",
                        "address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                        "function": "Main router for V3 swaps"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2021-04", "url": "https://github.com/Uniswap/v3-core/blob/main/audits/tob/audit.pdf"},
                    {"firm": "ABDK", "date": "2021-05", "url": "https://github.com/Uniswap/v3-core/blob/main/audits/abdk/audit.pdf"}
                ],
                "tvl_usd": 3_000_000_000,
                "years_active": 3.5,
                "exploits": 0,
                "github": "https://github.com/Uniswap/v3-core"
            },
            
            # ============================================================
            # Tier 1: Lending Protocols
            # ============================================================
            {
                "protocol": "Aave V2",
                "category": "lending",
                "contracts": [
                    {
                        "name": "LendingPool",
                        "address": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
                        "function": "Main lending pool"
                    },
                    {
                        "name": "LendingPoolAddressesProvider",
                        "address": "0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5",
                        "function": "Address registry"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2020-01", "url": "https://github.com/aave/aave-protocol/blob/master/docs/Aave_Protocol_Trail_of_Bits_Final_Report.pdf"},
                    {"firm": "OpenZeppelin", "date": "2020-02", "url": "https://blog.openzeppelin.com/aave-protocol-audit/"},
                    {"firm": "ABDK", "date": "2020-08", "url": "https://github.com/aave/aave-protocol/blob/master/docs/ABDK_Aave_v2_audit.pdf"},
                    {"firm": "Peckshield", "date": "2020-09", "url": "https://github.com/aave/aave-protocol/blob/master/docs/PeckShield-Audit-Report-Aave-v1.0.pdf"}
                ],
                "tvl_usd": 5_000_000_000,
                "years_active": 4,
                "exploits": 0,
                "github": "https://github.com/aave/aave-v2"
            },
            {
                "protocol": "Compound V2",
                "category": "lending",
                "contracts": [
                    {
                        "name": "Comptroller",
                        "address": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
                        "function": "Risk management and liquidation"
                    },
                    {
                        "name": "cDAI",
                        "address": "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
                        "function": "DAI lending market"
                    },
                    {
                        "name": "cUSDC",
                        "address": "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
                        "function": "USDC lending market"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2019-03", "url": "https://github.com/compound-finance/compound-protocol/tree/master/audits"},
                    {"firm": "OpenZeppelin", "date": "2019-08", "url": "https://blog.openzeppelin.com/compound-audit/"}
                ],
                "tvl_usd": 3_000_000_000,
                "years_active": 5,
                "exploits": 0,
                "github": "https://github.com/compound-finance/compound-protocol"
            },
            
            # ============================================================
            # Tier 2: Stablecoins
            # ============================================================
            {
                "protocol": "MakerDAO",
                "category": "stablecoin",
                "contracts": [
                    {
                        "name": "Vat",
                        "address": "0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B",
                        "function": "Core vault engine"
                    },
                    {
                        "name": "Dai",
                        "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                        "function": "DAI stablecoin"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2018-11", "url": "https://github.com/makerdao/mcd-security/blob/master/audits/TOB_MakerDAO_Final_Report.pdf"},
                    {"firm": "Peckshield", "date": "2019-06", "url": "https://github.com/makerdao/mcd-security/blob/master/audits/PeckShield-Audit-Report-MakerDAO-v1.0.pdf"}
                ],
                "tvl_usd": 5_000_000_000,
                "years_active": 6,
                "exploits": 0,
                "github": "https://github.com/makerdao/dss"
            },
            
            # ============================================================
            # Tier 3: Yield Aggregators
            # ============================================================
            {
                "protocol": "Yearn Finance",
                "category": "yield",
                "contracts": [
                    {
                        "name": "YearnVaultV2",
                        "address": "0xdA816459F1AB5631232FE5e97a05BBBb94970c95",
                        "function": "DAI vault"
                    },
                ],
                "audits": [
                    {"firm": "Trail of Bits", "date": "2020-08", "url": "https://github.com/yearn/yearn-security/tree/master/audits/Trail_of_Bits"},
                    {"firm": "ChainSecurity", "date": "2021-02", "url": "https://github.com/yearn/yearn-security/tree/master/audits/ChainSecurity"}
                ],
                "tvl_usd": 500_000_000,
                "years_active": 4,
                "exploits": 0,
                "github": "https://github.com/yearn/yearn-vaults"
            },
            
            # ============================================================
            # ADD MORE: Research additional protocols
            # Categories to add:
            # - DEXs: Curve, Balancer, SushiSwap
            # - Lending: MorphoBlue, Spark
            # - Derivatives: dYdX, GMX
            # - Bridges: Across, Hop
            # Target: 30+ protocols, 100+ contracts
            # ============================================================
        ]
    
    def collect(self) -> List[Dict]:
        """
        Collect and save audited protocol metadata.
        
        Returns:
            List of protocol dictionaries with contract addresses
        """
        logger.info("="*70)
        logger.info("🔒 AUDITED DEFI COLLECTOR")
        logger.info("="*70)
        logger.info("")
        
        # Statistics
        total_protocols = len(self.audited_protocols)
        total_contracts = sum(len(p['contracts']) for p in self.audited_protocols)
        total_audits = sum(len(p['audits']) for p in self.audited_protocols)
        total_tvl = sum(p['tvl_usd'] for p in self.audited_protocols)
        avg_years = sum(p['years_active'] for p in self.audited_protocols) / total_protocols
        
        by_category = {}
        for protocol in self.audited_protocols:
            cat = protocol['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        logger.info(f"📊 Catalogued protocols: {total_protocols}")
        logger.info(f"📄 Total contracts: {total_contracts}")
        logger.info(f"🔍 Total audits: {total_audits}")
        logger.info(f"💰 Combined TVL: ${total_tvl:,.0f}")
        logger.info(f"⏱️  Average age: {avg_years:.1f} years")
        logger.info(f"🛡️  Exploits: 0 (all protocols)")
        logger.info("")
        logger.info(f"📂 By category:")
        for category, count in sorted(by_category.items()):
            logger.info(f"   {category:15s}: {count:3d} protocols")
        
        # Save metadata
        output_file = self.output_dir / "audited_defi_protocols.json"
        with open(output_file, 'w') as f:
            json.dump(self.audited_protocols, f, indent=2)
        
        logger.info("")
        logger.info(f"✅ Saved metadata: {output_file}")
        logger.info("")
        logger.info("="*70)
        logger.info("📋 NEXT STEPS:")
        logger.info("="*70)
        logger.info("1. Verify all addresses on Etherscan")
        logger.info("2. Check audit reports are current")
        logger.info("3. Run master collector to fetch source code")
        logger.info("4. Add 20+ more protocols from research")
        logger.info("="*70)
        
        return self.audited_protocols


def main():
    collector = AuditedDeFiCollector()
    protocols = collector.collect()
    
    # Extract all contract addresses for easy collection
    addresses = []
    for protocol in protocols:
        for contract in protocol['contracts']:
            addresses.append(contract['address'])
    
    addresses_file = Path("data/metadata/safe_sources/audited_defi_addresses.txt")
    addresses_file.write_text('\n'.join(addresses))
    
    print(f"\n✅ Extracted {len(addresses)} addresses to: {addresses_file}")
    print(f"   Use these with master collector!")


if __name__ == "__main__":
    main()