# src/chainguardian/database/models.py
"""
Database models using SQLAlchemy ORM.

🎓 ORM (Object-Relational Mapping): Write Python classes, get SQL tables
Instead of writing CREATE TABLE queries, define classes

Why ORM vs raw SQL:
- Type safety (editor autocomplete)
- Migration management (Alembic tracks changes)
- Relationship handling (auto-join queries)
- Protection against SQL injection
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, Boolean, Float, 
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all models.
    
    🎓 Similar to Solidity inheritance:
    contract ERC20 is Base { ... }
    """
    pass


class Contract(Base):
    """
    Represents a smart contract in the database.

    🎓 DATABASE TABLE DESIGN:
    This is like a struct in Solidity:
    struct Contract {
        uint256 id;
        address contractAddress;
        string name;
        string sourceCode;
        // ... more fields
    }

    But SQLAlchemy ORM adds powerful features:
    - Auto-increment ID (like Solidity's counter++)
    - Unique constraints (prevent duplicate addresses)
    - Indexes (fast lookups by address)
    - Relationships (one contract → many features)
    - Timestamps (track when data was collected)
    - Cascade deletes (delete contract → auto-delete features)

    Why separate Contract and Features tables?
    - Normalization: Avoid duplicate contract data
    - Flexibility: Add new features without changing Contract table
    - Query optimization: Index frequently queried fields
    """

    __tablename__ = "contracts"

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    # 🎓 Auto-increment ID (1, 2, 3, ...)
    # Similar to Solidity: uint256 nextId; contracts[nextId++] = newContract;
    id: Mapped[int] = mapped_column(primary_key=True)

    # ========================================================================
    # CONTRACT METADATA
    # ========================================================================
    # 🎓 Ethereum address (42 chars: 0x + 40 hex digits)
    # unique=True: Prevents same contract being stored twice
    # index=True: Creates B-tree index for fast lookups
    #   Without index: O(n) scan entire table
    #   With index: O(log n) binary search
    address: Mapped[str] = mapped_column(String(42), unique=True, index=True)

    # Contract name (e.g., "UniswapV2Router", "USDT")
    name: Mapped[str] = mapped_column(String(255))

    # Full Solidity source code
    # Text type: Unlimited length (vs VARCHAR which has max length)
    source_code: Mapped[str] = mapped_column(Text)

    # Solidity compiler version (e.g., "0.8.19")
    compiler_version: Mapped[str] = mapped_column(String(50))

    # ========================================================================
    # DATA LINEAGE (track where data came from)
    # ========================================================================
    # 🎓 Production best practice: Always track data source!
    # Examples: 'etherscan', 'defilama', 'smartbugs', 'manual'
    source: Mapped[str] = mapped_column(String(50))

    # When was this contract collected?
    # 🎓 default=datetime.utcnow: Auto-set on INSERT
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Local file path (optional, for cached .sol files)
    # 🎓 Optional[str] + nullable=True: This field can be NULL
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ========================================================================
    # RELATIONSHIPS (ORM magic!)
    # ========================================================================
    # 🎓 Similar to Solidity mapping:
    # mapping(uint256 contractId => Feature[]) public contractFeatures;
    #
    # cascade="all, delete-orphan": If you delete a Contract,
    # automatically delete all its Features and Labels
    # (Like Solidity's selfdestruct cascade effect)
    features = relationship("ContractFeature", back_populates="contract", cascade="all, delete-orphan")
    labels = relationship("VulnerabilityLabel", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract(id={self.id}, name={self.name}, address={self.address})>"


class ContractFeature(Base):
    """
    Features extracted from a contract (Layer 1, 2, or 3).
    
    🎓 Why separate table instead of columns in Contract?
    - Features evolve (Layer 1: 50 features, Layer 2: +30, Layer 3: +700)
    - Easier to query specific layers
    - Avoid wide tables (50+ columns is hard to manage)
    """
    
    __tablename__ = "contract_features"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True)
    
    # Feature layer (1, 2, or 3)
    layer: Mapped[int] = mapped_column(Integer)
    
    # Feature name (e.g., 'num_functions', 'slither_reentrancy_count')
    feature_name: Mapped[str] = mapped_column(String(100))
    
    # Feature value (stored as string, convert to int/float/bool as needed)
    # 🎓 Similar to bytes in Solidity (generic storage)
    feature_value: Mapped[str] = mapped_column(Text)
    
    # Extraction metadata
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extraction_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationship back to contract
    contract = relationship("Contract", back_populates="features")
    
    # Unique constraint: one feature per (contract, layer, feature_name)
    __table_args__ = (
        UniqueConstraint('contract_id', 'layer', 'feature_name', name='uq_contract_layer_feature'),
        Index('idx_contract_layer', 'contract_id', 'layer'),  # Fast queries by layer
    )
    
    def __repr__(self):
        return f"<ContractFeature(contract_id={self.contract_id}, layer={self.layer}, {self.feature_name}={self.feature_value})>"


class VulnerabilityLabel(Base):
    """
    Ground truth labels for training ML models.

    🎓 MULTI-LABEL CLASSIFICATION:
    A single contract can have multiple vulnerabilities simultaneously:
    - Reentrancy: True
    - Access Control: True
    - Integer Overflow: False
    - Unchecked Send: True
    - ...

    This is different from multi-class (where only ONE can be true)

    Solidity equivalent:
    mapping(uint256 contractId => mapping(VulnType => bool)) public labels;

    GROUND TRUTH SOURCES:
    - Manual audits (high confidence, expensive)
    - Verified exploits (highest confidence)
    - Static analysis tools (medium confidence, can have false positives)
    - Community reports (varies)

    Why track source? Different sources have different reliability!
    """

    __tablename__ = "vulnerability_labels"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key to contracts table
    # 🎓 ForeignKey: Enforces referential integrity
    # You can't insert a label for a contract that doesn't exist!
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True)

    # ========================================================================
    # VULNERABILITY CLASSIFICATION
    # ========================================================================
    # Vulnerability type (enum-like string)
    # Examples: 'reentrancy', 'access_control', 'integer_overflow', etc.
    # 🎓 Why string instead of ENUM type?
    # - Flexibility: Easy to add new vulnerability types
    # - Portability: Works across all databases
    vulnerability_type: Mapped[str] = mapped_column(String(50))

    # Binary label: Does this contract have this vulnerability?
    # 🎓 This is your ML training target (y_true)
    has_vulnerability: Mapped[bool] = mapped_column(Boolean)

    # ========================================================================
    # METADATA (optional but recommended)
    # ========================================================================
    # Severity: How bad is this vulnerability?
    # 🎓 Optional because not all sources provide severity
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'high', 'medium', 'low'

    # Confidence: How sure are we about this label?
    # 🎓 Use for weighted loss functions in ML
    # Example: Manual audit = 1.0, automated tool = 0.7
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 - 1.0

    # Label source: Who/what labeled this?
    # 🎓 CRITICAL for data quality tracking!
    # Examples: 'manual_audit', 'slither', 'mythril', 'verified_exploit'
    source: Mapped[str] = mapped_column(String(50))

    # When was this labeled?
    labeled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship back to contract
    contract = relationship("Contract", back_populates="labels")

    # ========================================================================
    # CONSTRAINTS (data integrity rules)
    # ========================================================================
    # 🎓 Unique constraint: Prevent duplicate labels
    # Same contract can't have the same vulnerability type from same source twice
    # (But CAN have same type from different sources - e.g., Slither AND manual audit)
    __table_args__ = (
        UniqueConstraint('contract_id', 'vulnerability_type', 'source', name='uq_contract_vuln_source'),
        # Composite index for fast queries: "Get all reentrancy labels"
        Index('idx_contract_vuln', 'contract_id', 'vulnerability_type'),
    )

    def __repr__(self):
        return f"<VulnerabilityLabel(contract_id={self.contract_id}, type={self.vulnerability_type}, has={self.has_vulnerability})>"


class CollectionRun(Base):
    """
    Audit trail for data collection runs.

    🎓 PRODUCTION MONITORING BEST PRACTICE:
    Always track operational metadata for data pipelines!

    Critical questions this answers:
    - When did collection run?
    - How many contracts were processed?
    - What was the success/failure rate?
    - Were there errors? What were they?
    - Which data source was used?

    Why this matters:
    1. Debugging: If ML model performance drops, check collection runs
    2. Reliability: Track failure patterns (e.g., Etherscan API timeouts)
    3. Audit: Compliance requirements for data lineage
    4. Cost tracking: Monitor API usage and costs

    Similar to Solidity events:
    event CollectionCompleted(uint256 timestamp, uint256 successCount, uint256 failCount);

    But database tables > events because:
    - Queryable: "Show all failed runs in last 30 days"
    - Mutable: Update status as collection progresses
    - Relational: Join with contracts to see what was collected
    """

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ========================================================================
    # RUN METADATA
    # ========================================================================
    # Which data collector ran? (e.g., 'etherscan', 'defilama', 'smartbugs')
    source: Mapped[str] = mapped_column(String(50))

    # Timestamps for duration tracking
    # 🎓 started_at has default, completed_at is NULL until run finishes
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ========================================================================
    # RESULTS TRACKING
    # ========================================================================
    # 🎓 Track success/failure ratio for monitoring
    # attempted = succeeded + failed (sanity check)
    contracts_attempted: Mapped[int] = mapped_column(Integer, default=0)
    contracts_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    contracts_failed: Mapped[int] = mapped_column(Integer, default=0)

    # ========================================================================
    # STATUS AND ERROR HANDLING
    # ========================================================================
    # Current status: 'running', 'completed', 'failed'
    # 🎓 Use this to detect stuck runs (still 'running' after 24 hours)
    status: Mapped[str] = mapped_column(String(20))

    # Error message if collection failed
    # 🎓 Store full stack trace for debugging
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<CollectionRun(id={self.id}, source={self.source}, status={self.status})>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate as percentage."""
        if self.contracts_attempted > 0:
            return (self.contracts_succeeded / self.contracts_attempted) * 100
        return None