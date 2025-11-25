# PropFirm Scraper - Complete Database Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROPFIRM SCRAPER SYSTEM                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐
│  WEB SCRAPER    │      │  NORMALIZATION   │      │   DATABASE   │
│  (Playwright)   │─────▶│  & DEDUPLICATION │─────▶│   (SQLite)   │
│                 │      │                  │      │              │
│  • Cloudflare   │      │  • Canonicalize  │      │  • prop_firm │
│    bypass       │      │    URLs          │      │  • documents │
│  • Stealth mode │      │  • Hash content  │      │  • paragraphs│
│  • Follow links │      │  • Detect dupes  │      │  • firm_rule │
└─────────────────┘      └──────────────────┘      └──────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐
│  JSON OUTPUT    │      │  CONTENT HASH    │      │  QUERY API   │
│                 │      │                  │      │              │
│  • 356 pages    │      │  SHA256 hash     │      │  • Search    │
│  • Raw HTML/text│      │  for change      │      │  • Filter    │
│  • Metadata     │      │  detection       │      │  • Export    │
└─────────────────┘      └──────────────────┘      └──────────────┘
```

## Data Flow

```
1. SCRAPING
   ┌────────────────────────────────────────┐
   │  https://help.fundednext.com/en        │
   │                                        │
   │  • Crawl all help articles             │
   │  • Extract title, body, URL            │
   │  • Follow internal links               │
   │  • Save to JSON                        │
   └────────────────────────────────────────┘
                    │
                    │ 356 pages scraped
                    ▼
2. NORMALIZATION
   ┌────────────────────────────────────────┐
   │  URL Canonicalization                  │
   │                                        │
   │  Before:                               │
   │    /articles/123?ref=twitter#main      │
   │    /articles/123#section               │
   │    /articles/123/                      │
   │                                        │
   │  After:                                │
   │    /articles/123                       │
   │                                        │
   │  Result: 29 duplicates identified      │
   └────────────────────────────────────────┘
                    │
                    │ 327 unique documents
                    ▼
3. STORAGE
   ┌────────────────────────────────────────┐
   │  Database Tables                       │
   │                                        │
   │  prop_firm (1 firm)                    │
   │    └─▶ FundedNext                      │
   │                                        │
   │  help_document (327 docs)              │
   │    ├─▶ URL + base_url                  │
   │    ├─▶ title + body_text               │
   │    ├─▶ content_hash (SHA256)           │
   │    ├─▶ doc_type, version               │
   │    └─▶ timestamps                      │
   │                                        │
   │  document_paragraph (2,810 paras)      │
   │    ├─▶ paragraph_text                  │
   │    ├─▶ paragraph_index                 │
   │    └─▶ paragraph_hash                  │
   └────────────────────────────────────────┘
```

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROP_FIRM TABLE                             │
├─────────────────────────────────────────────────────────────────┤
│  id (PK)          │ 1                                            │
│  name             │ "FundedNext"                                 │
│  domain           │ "help.fundednext.com"                        │
│  website_url      │ "https://fundednext.com"                     │
│  help_center_url  │ "https://help.fundednext.com"                │
│  created_at       │ 2025-01-15 10:30:00                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │ firm_id (FK)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HELP_DOCUMENT TABLE (327 docs)                 │
├─────────────────────────────────────────────────────────────────┤
│  id (PK)          │ 1, 2, 3, ..., 327                            │
│  firm_id (FK)     │ 1 → FundedNext                               │
│  url              │ "...?ref=twitter" (original)                 │
│  base_url         │ "..." (canonicalized) ◄─ Used for dedup     │
│  title            │ "What is the profit target?"                 │
│  doc_type         │ "article" | "collection" | "homepage"        │
│  body_text        │ Full document content                        │
│  content_hash     │ "a3f5b8..." (SHA256) ◄─ For change detection│
│  scraped_at       │ 2025-01-15 10:35:22                          │
│  first_seen_at    │ 2025-01-15 10:35:22                          │
│  last_updated_at  │ 2025-01-15 10:35:22                          │
│  is_current       │ 1 (boolean) ◄─ For versioning               │
│  version          │ 1, 2, 3, ... ◄─ Increments on changes       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │ document_id (FK)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              DOCUMENT_PARAGRAPH TABLE (2,810 paras)              │
├─────────────────────────────────────────────────────────────────┤
│  id (PK)          │ 1, 2, 3, ..., 2810                           │
│  document_id (FK) │ 1, 1, 1, 2, 2, 2, ...                        │
│  paragraph_index  │ 0, 1, 2, 0, 1, 2, ... ◄─ Order in doc       │
│  paragraph_text   │ "The profit target is..."                    │
│  paragraph_hash   │ "b7e2c9..." (SHA256)                         │
│  created_at       │ 2025-01-15 10:35:22                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│          FIRM_RULE TABLE (for future rule extraction)            │
├─────────────────────────────────────────────────────────────────┤
│  id (PK)              │ Ready for structured rules               │
│  firm_id (FK)         │ → Links to prop_firm                     │
│  source_document_id   │ → Links to help_document                 │
│  rule_type            │ "profit_target", "daily_loss", etc.      │
│  rule_category        │ "hard_rule", "soft_rule", "guideline"    │
│  challenge_type       │ "stellar_1_step", "stellar_2_step", etc. │
│  value                │ "10%", "$50000", etc.                    │
│  details              │ Full rule explanation                    │
│  extraction_method    │ "pattern", "llm", "hybrid", "manual"     │
│  confidence_score     │ 0.0 - 1.0                                │
└─────────────────────────────────────────────────────────────────┘
```

## URL Canonicalization Process

```
INPUT URLS (from scraping):
────────────────────────────────────────────────────────────────
https://help.fundednext.com/en/articles/8755881?msclkid=abc123
https://help.fundednext.com/en/articles/8755881?ref=twitter
https://help.fundednext.com/en/articles/8755881#main-content
https://help.fundednext.com/en/articles/8755881#h_section_2
https://help.fundednext.com/en/articles/8755881/

                            ▼
                    CANONICALIZATION
                    ────────────────
                    1. Remove query params (?)
                    2. Remove fragments (#)
                    3. Remove trailing slash
                    4. Normalize case

                            ▼
CANONICAL URL (stored in base_url):
────────────────────────────────────────────────────────────────
https://help.fundednext.com/en/articles/8755881

RESULT: 5 URLs → 1 unique document (4 duplicates eliminated)
```

## Content Hashing for Change Detection

```
DOCUMENT v1 (initial scrape):
────────────────────────────────────────────────────────────────
Content: "The profit target is 10% for all challenge accounts."
Hash:    a3f5b8c2e7d1f9...  ◄─ SHA256 hash stored

                            ▼
RE-SCRAPING (later):
────────────────────────────────────────────────────────────────
Content: "The profit target is 10% for all challenge accounts."
Hash:    a3f5b8c2e7d1f9...  ◄─ Same hash

RESULT: No change detected, skip insert (duplicate)

────────────────────────────────────────────────────────────────
DOCUMENT v2 (content updated):
────────────────────────────────────────────────────────────────
Content: "The profit target is 8% for all challenge accounts."
Hash:    d9c7e4a1b8f2c3...  ◄─ Different hash

RESULT: Change detected!
        1. Mark v1 as is_current = 0
        2. Insert v2 with version = 2, is_current = 1
        3. Preserve first_seen_at from v1

VERSION HISTORY:
┌─────────┬──────────┬────────────┬──────────────────────────┐
│ Version │ Current  │ Hash       │ Content                  │
├─────────┼──────────┼────────────┼──────────────────────────┤
│    1    │    No    │ a3f5b8c2...│ "...target is 10%..."    │
│    2    │   Yes    │ d9c7e4a1...│ "...target is 8%..."     │
└─────────┴──────────┴────────────┴──────────────────────────┘
```

## Query & Retrieval Patterns

```
USE CASE 1: Get all current documents
─────────────────────────────────────────────────────────────
SELECT * FROM help_document 
WHERE is_current = 1 AND firm_id = 1
ORDER BY title;

Returns: 327 documents (latest versions only)

────────────────────────────────────────────────────────────
USE CASE 2: Search for specific content
─────────────────────────────────────────────────────────────
SELECT * FROM help_document
WHERE is_current = 1 
AND (title LIKE '%profit target%' OR body_text LIKE '%profit target%');

Returns: 61 matching documents

────────────────────────────────────────────────────────────
USE CASE 3: Get paragraphs for RAG
─────────────────────────────────────────────────────────────
SELECT p.paragraph_text, d.title, d.base_url
FROM document_paragraph p
JOIN help_document d ON p.document_id = d.id
WHERE d.is_current = 1
ORDER BY p.document_id, p.paragraph_index;

Returns: 2,810 paragraphs with context

────────────────────────────────────────────────────────────
USE CASE 4: Track document changes
─────────────────────────────────────────────────────────────
SELECT base_url, COUNT(*) as versions
FROM help_document
GROUP BY base_url
HAVING versions > 1;

Returns: Documents that have changed over time
```

## Integration Points

```
┌──────────────────────────────────────────────────────────────┐
│                    FUTURE INTEGRATIONS                        │
└──────────────────────────────────────────────────────────────┘

1. RULE EXTRACTION PIPELINE
   ┌────────────────────┐
   │  Database          │
   │  └─▶ Documents     │───▶ Hybrid Extractor ───▶ firm_rule table
   │      (327 docs)    │         (pattern + LLM)
   └────────────────────┘

2. RAG EMBEDDINGS
   ┌────────────────────┐
   │  Database          │
   │  └─▶ Paragraphs    │───▶ OpenAI API ───▶ Vector DB
   │      (2,810 paras) │      (embeddings)    (Pinecone/Weaviate)
   └────────────────────┘

3. CHANGE MONITORING
   ┌────────────────────┐
   │  Re-scrape Daily   │───▶ Compare hashes ───▶ Alert on changes
   │  └─▶ New JSON      │      (automatic)
   └────────────────────┘

4. MULTI-FIRM COMPARISON
   ┌────────────────────┐
   │  Add More Firms    │
   │  ├─▶ FTMO          │───▶ Comparative analysis
   │  ├─▶ MyForexFunds  │      (rules, policies)
   │  └─▶ TopStepFX     │
   └────────────────────┘
```

## Performance Characteristics

```
OPERATION                  TIME        THROUGHPUT
──────────────────────────────────────────────────────────────
Initial ingestion          15s         ~24 docs/sec
Re-ingestion (no changes)  5s          ~71 docs/sec
Search query               0.3s        Instant
Get all documents          0.2s        ~1,635 docs/sec
Database size              2.34 MB     Highly compressed
Deduplication rate         8.1%        29/356 duplicates
```

## File Structure

```
propfirm-scraper/
│
├── database/                      ◄─ NEW: Database module
│   ├── schema.sql                 ◄─ Database schema
│   ├── db_utils.py                ◄─ URL/hash utilities
│   ├── ingest_documents.py        ◄─ Ingestion engine
│   ├── query_db.py                ◄─ Query interface
│   ├── analyze_db.py              ◄─ Content analysis
│   ├── examples.py                ◄─ Usage examples
│   ├── README.md                  ◄─ Full documentation
│   ├── SETUP_COMPLETE.md          ◄─ Quick start
│   └── propfirm_scraper.db       ◄─ SQLite database
│
├── src/                           ◄─ Existing: Scraper & extractors
│   ├── scraper.py
│   ├── hybrid_extractor.py
│   ├── fast_extractor.py
│   └── ...
│
├── output/                        ◄─ Scraped JSON files
│   └── fundednext_complete.json
│
└── DATABASE_COMPLETE.md           ◄─ This file
```

---

**Status**: ✅ Fully implemented and operational
**Next Step**: Integrate with rule extraction or create RAG embeddings
