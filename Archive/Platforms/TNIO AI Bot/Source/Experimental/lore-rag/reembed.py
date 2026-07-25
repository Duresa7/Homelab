import time, sys
sys.path.insert(0, '/home/REDACTED_DEPLOYMENT_USER/lore-rag')
import sync_lore

chunks = sync_lore.load_chunks()
print(f"chunks loaded: {len(chunks)}", flush=True)
coll = sync_lore.collection()
print(f"new collection starts at: {coll.count()} vectors", flush=True)

batch_size = 16
texts = [c["text"] for c in chunks]
ids = [c["chunk_id"] for c in chunks]
metas = [c["metadata"] for c in chunks]

t0 = time.time()
total = 0
errors = 0
for i in range(0, len(chunks), batch_size):
    btxts = texts[i:i+batch_size]
    try:
        embs = sync_lore.embed_texts(btxts)
        if len(embs) != len(btxts):
            errors += 1
            continue
        coll.upsert(ids=ids[i:i+batch_size], embeddings=embs, documents=btxts, metadatas=metas[i:i+batch_size])
        total += len(btxts)
    except Exception as exc:
        print(f"batch {i}: {exc}", flush=True)
        errors += 1
    if (i // batch_size) % 10 == 0:
        elapsed = time.time() - t0
        rate = total / max(0.01, elapsed)
        print(f"  {total}/{len(chunks)} {rate:.1f}/s elapsed={elapsed:.0f}s", flush=True)

elapsed = time.time() - t0
print(f"DONE total={total} errors={errors} elapsed={elapsed:.1f}s rate={total/max(0.01,elapsed):.1f}/s", flush=True)
print(f"final collection count: {coll.count()}", flush=True)
