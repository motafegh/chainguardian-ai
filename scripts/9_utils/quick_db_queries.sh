#!/bin/bash
# Quick Database Verification Queries
# Usage: bash scripts/9_utils/quick_db_queries.sh

DB_USER="chainguardian_user"
DB_NAME="chainguardian"
DB_PASSWORD="2220128"
DB_HOST="localhost"  # Force TCP connection

echo "======================================================================"
echo "CHAINGUARDIAN DATABASE QUICK QUERIES"
echo "======================================================================"

# Query 1: Contract counts by source
echo -e "\n1️⃣  CONTRACT COUNTS BY SOURCE"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    data_source,
    COUNT(*) as total,
    COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) as successful,
    ROUND(100.0 * COUNT(CASE WHEN f.failure_reason IS NULL THEN 1 END) / COUNT(*), 1) as success_rate
FROM contracts c
LEFT JOIN features f ON c.id = f.contract_id
GROUP BY data_source
ORDER BY data_source;
"

# Query 2: Label distribution
echo -e "\n2️⃣  LABEL DISTRIBUTION (for ML)"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    CASE 
        WHEN data_source IN ('smartbugs_curated', 'production_vulnerable', 'trail_of_bits') 
        THEN 'VULNERABLE'
        ELSE 'SAFE'
    END as label,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM contracts c
INNER JOIN features f ON c.id = f.contract_id
WHERE f.failure_reason IS NULL
GROUP BY label;
"

# Query 3: CEI violations (your innovation)
echo -e "\n3️⃣  CEI VIOLATIONS DETECTED"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    c.name,
    c.data_source,
    f.cei_violations,
    f.cei_pattern_score,
    f.has_reentrancy_guard,
    f.state_after_call_count
FROM contracts c
INNER JOIN features f ON c.id = f.contract_id
WHERE f.cei_violations > 0
ORDER BY f.cei_violations DESC;
"

# Query 4: Feature completeness
echo -e "\n4️⃣  FEATURE COMPLETENESS CHECK"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN lines_of_code IS NULL THEN 1 END) as null_loc,
    COUNT(CASE WHEN cei_violations IS NULL THEN 1 END) as null_cei,
    COUNT(CASE WHEN has_reentrancy IS NULL THEN 1 END) as null_reentrancy
FROM features
WHERE failure_reason IS NULL;
"

# Query 5: Top vulnerable contracts (by risk score)
echo -e "\n5️⃣  TOP 10 HIGHEST RISK CONTRACTS"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    c.name,
    c.data_source,
    f.risk_score_weighted,
    f.cei_violations,
    f.total_detector_hits
FROM contracts c
INNER JOIN features f ON c.id = f.contract_id
WHERE f.failure_reason IS NULL
ORDER BY f.risk_score_weighted DESC
LIMIT 10;
"

# Query 6: Feature statistics
echo -e "\n6️⃣  FEATURE STATISTICS"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    'lines_of_code' as feature,
    MIN(lines_of_code) as min,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lines_of_code)) as median,
    MAX(lines_of_code) as max
FROM features WHERE failure_reason IS NULL
UNION ALL
SELECT 
    'num_functions',
    MIN(num_functions),
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY num_functions)),
    MAX(num_functions)
FROM features WHERE failure_reason IS NULL
UNION ALL
SELECT 
    'cei_violations',
    MIN(cei_violations),
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cei_violations)),
    MAX(cei_violations)
FROM features WHERE failure_reason IS NULL;
"

# Query 7: Database size
echo -e "\n7️⃣  DATABASE SIZE"
echo "----------------------------------------------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    pg_size_pretty(pg_database_size('chainguardian')) as database_size,
    pg_size_pretty(pg_total_relation_size('contracts')) as contracts_table_size,
    pg_size_pretty(pg_total_relation_size('features')) as features_table_size;
"

echo -e "\n======================================================================"
echo "✅ QUERIES COMPLETE"
echo "======================================================================"
