# FAQ Chatbot — Technical Strategy

## What We Are Building

A chatbot that answers user questions by matching them against a predefined set of FAQ entries. It does **not** generate answers from scratch — it retrieves the best matching answer from your knowledge base.

---

## Core Concept

When a user asks a question, the system finds the most semantically similar question in your FAQ database and returns its answer.

The key word here is **semantically** — we are not comparing words, we are comparing **meaning**.


---

## The Strategy: Embedding-Based Matching

### Step 1 — Embed your FAQ questions

Convert each FAQ question into a **vector** — a list of numbers that mathematically represents its meaning. This is done using a pre-trained embedding model.

> You do **not** train this model yourself. You use a pre-trained one that already understands language semantics. This is the standard professional approach.

**Recommended free option:** [Sentence Transformers](https://www.sbert.net/) — open source, runs locally, no cost, and quality is competitive with paid APIs.

You only do this **once**. Then you store the vectors.

### Step 2 — Store the vectors

Save each FAQ entry alongside its vector in your database. The question, the answer, and the vector all live together.

### Step 3 — Handle a user query

When a user asks something:

1. Embed their question using the **same** embedding model
2. Compare their vector against all stored FAQ vectors
3. Find the **closest match** using cosine similarity
4. Return the answer linked to that closest FAQ entry

---

## How Similarity Works

**Cosine similarity** measures how "close" two vectors are in meaning — not in exact wording.

- Score close to **1** → very similar meaning → good match
- Score close to **0** → very different meaning → no match

You can set a **threshold** (e.g., 0.75) below which the system replies "I don't know" instead of returning a bad match.

---

## Summary Flow

```
User query
    ↓
Embed query (pre-trained model)
    ↓
Compare vector to stored FAQ vectors (cosine similarity)
    ↓
Find closest match above threshold
    ↓
Return the corresponding answer
```

---

## Key Takeaways

| Topic                 | Decision                                 |
| --------------------- | ---------------------------------------- |
| Matching strategy     | Semantic similarity via embeddings       |
| Embedding model       | Pre-trained (e.g. Sentence Transformers) |
| Similarity metric     | Cosine similarity                        |
| Data needed           | 50–300 FAQ pairs                         |
| Training from scratch | Not needed                               |
| Cost                  | Can be fully free                        |