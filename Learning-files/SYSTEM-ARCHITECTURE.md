┌─────────────────────────────────────────────────────────────┐
│                      LAYER 1: ML CORE                        │
│  (Detect vulnerabilities using Machine Learning)            │
└─────────────────────────────────────────────────────────────┘
         │
         │ Raw Solidity Code
         ▼
    ┌─────────────┐
    │   Slither   │ ──> Extract 50+ features
    │   (Static   │     (reentrancy risk, access control, etc.)
    │   Analysis) │
    └─────────────┘
         │
         │ Feature Vector [0.2, 0.8, 0.1, ...]
         ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Random     │────>│  XGBoost    │────>│     GNN     │
    │  Forest     │     │  (Main)     │     │ (Advanced)  │
    │ (Baseline)  │     └─────────────┘     └─────────────┘
    └─────────────┘            │                    │
         │                     │                    │
         └─────────────────────┴────────────────────┘
                               │
                               │ Ensemble Vote
                               ▼
                        ┌─────────────┐
                        │  Prediction │
                        │  [High Risk]│
                        │  Score: 0.87│
                        └─────────────┘


┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: LLM + RAG                        │
│  (Generate human-readable audit reports)                    │
└─────────────────────────────────────────────────────────────┘
         │
         │ Vulnerability found: "Reentrancy in withdraw()"
         ▼
    ┌─────────────┐
    │ RAG System  │
    │             │
    │  Query: "Show me similar reentrancy exploits"
    │             │
    │  ┌────────────────────────────┐
    │  │ Vector DB (FAISS/Pinecone) │
    │  │ • DAO Hack 2016            │
    │  │ • Cream Finance 2021       │
    │  │ • 500+ historical exploits │
    │  └────────────────────────────┘
    └─────────────┘
         │
         │ Retrieved: 3 similar cases
         ▼
    ┌─────────────┐
    │ Fine-tuned  │  Prompt:
    │ Llama 3.2   │  "Generate audit report for reentrancy
    │ (LoRA)      │   vulnerability in withdraw() function.
    │             │   Similar to DAO Hack 2016..."
    └─────────────┘
         │
         │ Generated Report
         ▼
    ┌─────────────────────────────────────────────────┐
    │ AUDIT REPORT                                     │
    │                                                  │
    │ Vulnerability: Reentrancy in withdraw()         │
    │ Severity: HIGH                                   │
    │                                                  │
    │ Description:                                     │
    │ The withdraw() function calls external contract │
    │ before updating internal state...                │
    │                                                  │
    │ Similar Exploit: DAO Hack (2016) - $60M loss    │
    │                                                  │
    │ Recommendation:                                  │
    │ 1. Use Checks-Effects-Interactions pattern      │
    │ 2. Add ReentrancyGuard modifier                  │
    │ 3. Update balance before external call           │
    └─────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                  LAYER 3: BLOCKCHAIN                         │
│  (On-chain verification & trust)                            │
└─────────────────────────────────────────────────────────────┘
         │
         │ Audit Complete
         ▼
    ┌─────────────┐
    │ AuditRegistry│  Store on Ethereum:
    │ .sol         │  • Contract address
    │              │  • Risk score
    │              │  • Timestamp
    │              │  • IPFS hash (full report)
    └─────────────┘
         │
         │ Mint NFT Certificate
         ▼
    ┌─────────────┐
    │ Chainlink   │  Fetch ML prediction:
    │ Functions   │  GET chainguardian.ai/api/predict
    │             │  ──> Bring off-chain ML on-chain
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │ ZK Proof    │  Prove:
    │ Verifier    │  "This audit was performed correctly"
    │             │  without revealing model weights
    └─────────────┘