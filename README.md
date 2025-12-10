# ChainGuardian AI

> **Status:** 🚧 Active Development - Week 1/6  
> **Current Phase:** Feature extraction pipeline (Day 1 complete)

AI-powered smart contract auditing platform combining machine learning, fine-tuned LLMs, and blockchain verification.

---

## 🎯 Project Vision

Automated security auditing for Solidity smart contracts using:
- **ML ensemble** (Random Forest + XGBoost + GNN) for vulnerability detection
- **Fine-tuned Llama 3.2** for human-readable audit reports
- **RAG system** learning from historical exploit database
- **On-chain verification** via Chainlink oracles + ZK proofs
- **MLOps pipeline** for continuous model improvement

**Target:** Junior AI/ML Engineer roles (1-2 months), Smart Contract Auditor (6-12 months)

---

## ✅ Completed (Week 1, Day 1)

### Feature Extraction Pipeline
Extracts 15 ML-ready features from Solidity contracts:

**Binary Flags (4):**
- Reentrancy vulnerability
- Access control issues
- Timestamp dependency
- Unchecked external calls

**Severity Counts (3):**
- High/Medium/Low vulnerability counts

**Code Metrics (6):**
- Function count, external calls, low-level calls
- State variables, modifiers, cyclomatic complexity

**Example output:**
contract_name,has_reentrancy,high_severity_count,num_functions,...
VulnerableBank,True,3,7,...

text

**Technologies:** Python 3.12, Slither (static analysis), AST parsing

---

## 🚀 Quick Start (Current Features)

Clone repository
git clone https://github.com/motafegh/chainguardian-ai
cd chainguardian-ai

Install dependencies
poetry install

Analyze a contract
poetry run slither path/to/Contract.sol --json output.json

Extract features
poetry run python << 'PYEOF'
from pathlib import Path
from src.chainguardian.feature_extraction.pipeline import FeaturePipeline

pipeline = FeaturePipeline()
pipeline.analyze_contract(
contract_path=Path("path/to/Contract.sol"),
contract_name="ContractName",
json_output_path=Path("output.json")
)
df = pipeline.to_dataframe()
print(df)
PYEOF

text

---

## 📅 Development Roadmap

- [x] **Day 1:** Feature extraction pipeline (15 features)
- [ ] **Days 2-3:** Dataset collection (scrape 500+ contracts from Etherscan)
- [ ] **Days 4-7:** Train baseline models (Random Forest, XGBoost)
- [ ] **Days 8-12:** Hyperparameter tuning & evaluation
- [ ] **Week 3:** RAG system + LLM fine-tuning (Llama 3.2 + LoRA)
- [ ] **Week 4:** MLOps pipeline (Airflow, MLflow, monitoring)
- [ ] **Week 5:** Blockchain integration (Solidity contracts, Chainlink)
- [ ] **Week 6:** FastAPI backend + deployment

---

## 🛠️ Tech Stack (Planned)

**Core:**
- Python 3.12, Poetry
- PyTorch, scikit-learn, XGBoost
- Slither (static analysis)

**ML/LLM (Weeks 2-4):**
- Hugging Face Transformers
- LoRA fine-tuning
- FAISS/ChromaDB (vector DB)

**MLOps (Week 4):**
- Airflow (orchestration)
- MLflow (tracking)
- Docker

**Blockchain (Week 5):**
- Solidity 0.8.20+, Foundry
- Chainlink Functions

**Backend (Week 6):**
- FastAPI, PostgreSQL

---

## 📊 Project Structure

chainguardian-ai/
├── src/chainguardian/
│ └── feature_extraction/ # ✅ Day 1 (COMPLETE)
│ ├── contract_analyzer.py # Slither JSON parser
│ ├── ast_analyzer.py # AST feature extraction
│ └── pipeline.py # Unified orchestrator
├── blockchain/contracts/examples/
│ └── VulnerableBank.sol # Test contract
├── data/
│ └── vulnerable_bank_features.csv # First dataset
├── tests/
└── pyproject.toml

text

*Structure evolves as features are built.*

---

## 🎓 Learning Methodology

This project follows a **build-first, document-second** approach optimized for ADHD learning:
1. **Brief concept** (2-3 min)
2. **Build immediately** (code in 10-20 line chunks)
3. **Test & verify** (prove understanding)
4. **Interview prep** (resume bullets + Q&A frameworks)
5. **Document** (notebook entries)

See [Learning Notes](docs/learning_notes/) for daily progress.

---

## 📝 Key Learnings (Day 1)

**Technical:**
- Integrated Slither static analysis with Python API
- Built modular feature extraction pipeline with error isolation
- Debugged real-world tool integration issues (detector name mismatches)

**Architectural:**
- Dataclass pattern for structured features
- Defensive programming (short-circuit evaluation, try-except isolation)
- Evolutionary structure (add folders when needed, not upfront)

**Interview-Ready Skills:**
- Feature engineering for security ML
- AST parsing and code analysis
- Production pipeline design

---

## 👨‍💻 Author

**Ali Motafegh**  
Hybrid AI/Blockchain Engineer  
- 🐍 Python (ML/Backend)
- ⛓️ Solidity (7 months, DeFi + cross-chain)
- 🤖 Returning to ML after 2-3 year gap
- 🎯 Building portfolio for Junior AI/ML Engineer roles

**GitHub:** [@YourUsername](https://github.com/YourUsername)  
**Location:** Iran  
**Focus:** Practical, production-ready AI systems for Web3 security

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

**Last Updated:** December 10, 2025  
**Current Sprint:** Week 1 - ML Foundations  
**Next Milestone:** Dataset collection (500+ contracts by Day 3)
