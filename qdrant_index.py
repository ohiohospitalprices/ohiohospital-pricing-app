"""
Qdrant Vector Search Index Builder - GPU accelerated with all-MiniLM-L6-v2
First run: python qdrant_index.py  (indexes top procedures)
"""
import sqlite3, time, sys
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

QDRANT_URL = "https://3827842b-99bd-4705-a080-6cc2029482b9.us-west-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MGEzNzQ4NjItNzZiNi00OGEyLWE5NWQtZWQwODg4Yjg0ODVkIn0.v0-LhCBGraFw9k3wlLh-oJab38epNah3VWV7AhLp02E"
COLLECTION = "ohio_procedures"
DB = "hospital_pricing.db"
BATCH = 50
MAX_PROCS = 50000

def index():
    print("Loading sentence-transformers model on GPU...")
    t0 = time.time()
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")
    print(f"Loaded in {time.time()-t0:.1f}s")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    print("\nLoading top procedures by hospital coverage...")
    cursor.execute("""
        SELECT pt.id, pt.name, pt.cpt, pt.category,
            COUNT(DISTINCT pr.hospital_id) as hcount,
            MIN(pr.price) as min_p,
            ROUND(AVG(pr.price), 0) as avg_p,
            MAX(pr.price) as max_p
        FROM procedures_table pt
        JOIN pricing pr ON pt.id = pr.procedure_id
        WHERE pr.price > 0
        GROUP BY pt.id
        HAVING hcount > 0
        ORDER BY hcount DESC, AVG(pr.price) DESC
        LIMIT ?
    """, (MAX_PROCS,))
    procs = cursor.fetchall()
    print(f"Loading {len(procs):,} most-covered procedures")

    print("Loading hospital names...")
    cursor.execute("SELECT pr.procedure_id, h.name FROM pricing pr JOIN hospitals h ON pr.hospital_id = h.id WHERE pr.price > 0 ORDER BY pr.procedure_id")
    proc_hosp = {}
    for pid, hname in cursor.fetchall():
        if pid not in proc_hosp: proc_hosp[pid] = []
        if len(proc_hosp[pid]) < 5: proc_hosp[pid].append(hname)
    conn.close()

    print("Building search texts...")
    texts, data = [], []
    for pid, name, cpt, cat, hc, min_p, avg_p, max_p in procs:
        hosps = proc_hosp.get(pid, [])
        txt = f"{name} | {cat or 'General'} | ${min_p:,.0f} avg ${avg_p:,.0f} max ${max_p:,.0f} | {', '.join(hosps[:3])}"
        texts.append(txt)
        data.append({"pid": pid, "name": name[:300], "cpt": cpt or "", "cat": cat or "Other",
                      "hcount": hc, "min_p": float(min_p or 0), "avg_p": float(avg_p or 0),
                      "max_p": float(max_p or 0), "hosps": hosps[:5]})

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)
    try: client.delete_collection(COLLECTION)
    except: pass
    client.create_collection(collection_name=COLLECTION, vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    print("Qdrant collection ready.")

    t0, indexed, errors = time.time(), 0, 0
    print(f"\nIndexing {len(data):,} procedures...")
    for i in range(0, len(texts), BATCH):
        try:
            embs = model.encode(texts[i:i+BATCH], show_progress_bar=False, convert_to_numpy=True)
            points = [PointStruct(id=d["pid"], vector=emb.tolist(), payload={
                "procedure_name": d["name"], "cpt_code": d["cpt"], "category": d["cat"],
                "hospital_count": d["hcount"], "min_price": d["min_p"], "avg_price": d["avg_p"],
                "max_price": d["max_p"], "hospitals": d["hosps"]
            }) for emb, d in zip(embs, data[i:i+BATCH])]
            
            for attempt in range(3):
                try:
                    client.upsert(collection_name=COLLECTION, points=points)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(3 * (attempt + 1))
                    else:
                        raise e
            
            indexed += len(points)
        except Exception as e:
            errors += 1
            print(f"  Error batch {i}: {e}")
            time.sleep(10)

        if (i // BATCH) % 50 == 0 or indexed >= len(data):
            elapsed = time.time() - t0
            rate = indexed / elapsed if elapsed > 0 else 0
            pct = indexed / len(data) * 100
            eta = (len(data) - indexed) / rate if rate > 0 else 0
            print(f"  {indexed:,}/{len(data):,} ({pct:.1f}%) | {rate:.0f}/sec | ETA: {eta:.0f}s")

    elapsed = time.time() - t0
    print(f"\nDONE! Indexed {indexed:,} procedures in {elapsed:.0f}s")
    if errors: print(f"Errors: {errors}")

    # Quick test
    print("\nTest search: 'how much is an MRI'")
    emb = model.encode("how much is an MRI", convert_to_numpy=True)
    results = client.query_points(collection_name=COLLECTION, query=emb.tolist(), limit=5)
    for r in results.points:
        p = r.payload
        print(f"  [{p['cpt_code']}] {p['procedure_name'][:65]}")
        print(f"    ${p['min_price']:,.0f} - ${p['max_price']:,.0f} | score={r.score:.3f} | {p['hospital_count']} hosp")

if __name__ == "__main__":
    index()
