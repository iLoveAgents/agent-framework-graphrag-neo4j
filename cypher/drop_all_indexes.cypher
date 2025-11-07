// Drop All Indexes and Constraints
// Use this if you need to completely reset the database schema

// Show all indexes
SHOW INDEXES;

// Show all constraints
SHOW CONSTRAINTS;

// Drop all indexes (run each line individually or uncomment as needed)
// Note: You'll need to replace INDEX_NAME with actual index names from SHOW INDEXES

// Example: DROP INDEX index_name IF EXISTS;

// Drop vector indexes created by 02_build_graph.py
DROP INDEX excerptEmbeddingIndex IF EXISTS;

// Drop vector indexes created by SimpleKGPipeline (if any)
DROP INDEX chunk_embedding_index IF EXISTS;
