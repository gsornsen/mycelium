# Source: operations/coordination-tracking.md
# Line: 413
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: unexpected indent (<unknown>, line 2)

   # Use PostgreSQL query stats
   SELECT query, mean_exec_time
   FROM pg_stat_statements
   WHERE query LIKE '%coordination_events%';