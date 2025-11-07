// Reset Neo4j Database
// This query deletes all nodes and relationships from the database
// Use this to start fresh before running 02_build_graph.py or 02_build_graph_graphrag.py

// WARNING: This will DELETE ALL DATA in the current database!

// Delete all nodes and relationships
MATCH (n)
DETACH DELETE n;

// Verify database is empty
MATCH (n) RETURN count(n) as remaining_nodes;
