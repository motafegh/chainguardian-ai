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
    Represents a smart contract.
    
    🎓 This is like a struct in Solidity:
    struct Contract {
        uint256 id;
        address contractAddress;
        string name;
        string sourceCode;
        // ... more fields
    }
    
    But SQLAlchemy adds:
    - Auto-increment ID
    - Unique constraints
    - Relationships to other tables
    - Timestamps
    """
    
    __tablename__ = "contracts"
    
    # Primary key (auto-increment)
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Contract metadata
    address: Mapped[str] = mapped_column(String(42), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    source_code: Mapped[str] = mapped_column(Text)
    compiler_version: Mapped[str] = mapped_column(String(50))
    
    # Collection metadata
    source: Mapped[str] = mapped_column(String(50))  # 'defilama', 'etherscan', etc.
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # File paths (for local storage)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships (like foreign keys but Pythonic)
    # 🎓 Similar to: mapping(uint256 => Feature[]) in Solidity
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
    Ground truth labels for vulnerabilities.
    
    🎓 Multi-label classification:
    A contract can have multiple vulnerabilities:
    - Reentrancy: True
    - Access Control: True
    - Integer Overflow: False
    - ...
    
    This is like a mapping in Solidity:
    mapping(uint256 contractId => mapping(VulnType => bool))
    """
    
    __tablename__ = "vulnerability_labels"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True)
    
    # Vulnerability type (enum-like)
    vulnerability_type: Mapped[str] = mapped_column(String(50))  # 'reentrancy', 'access_control', etc.
    
    # Label (binary: has this vulnerability or not)
    has_vulnerability: Mapped[bool] = mapped_column(Boolean)
    
    # Confidence / severity (optional)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'high', 'medium', 'low'
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    
    # Label source (manual, slither, mythril, etc.)
    source: Mapped[str] = mapped_column(String(50))
    labeled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    contract = relationship("Contract", back_populates="labels")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('contract_id', 'vulnerability_type', 'source', name='uq_contract_vuln_source'),
        Index('idx_contract_vuln', 'contract_id', 'vulnerability_type'),
    )
    
    def __repr__(self):
        return f"<VulnerabilityLabel(contract_id={self.contract_id}, type={self.vulnerability_type}, has={self.has_vulnerability})>"


class CollectionRun(Base):
    """
    Track data collection runs for monitoring.
    
    🎓 Production best practice: Always track metadata
    - When did collection run?
    - How many contracts collected?
    - Were there errors?
    
    Similar to event logs in Solidity:
    event CollectionCompleted(uint256 timestamp, uint256 count);
    """
    
    __tablename__ = "collection_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Run metadata
    source: Mapped[str] = mapped_column(String(50))  # Which collector ran
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Results
    contracts_attempted: Mapped[int] = mapped_column(Integer, default=0)
    contracts_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    contracts_failed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(20))  # 'running', 'completed', 'failed'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self):
        return f"<CollectionRun(id={self.id}, source={self.source}, status={self.status})>"