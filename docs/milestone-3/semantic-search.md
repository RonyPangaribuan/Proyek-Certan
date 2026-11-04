# T03: Dense Embeddings dan Persistent Semantic Search

Pipeline yang tersedia: **chunk teks → embedding ternormalisasi → persistent
ChromaDB → pencarian semantik**. Ingestion dan word-aware chunking dari 15
dokumen nyata kini tersedia melalui [panduan korpus](./corpus-ingestion.md).
Contoh pengujian indexing di bawah masih menggunakan data sintetis; chunk
korpus nyata belum diindex atau diuji relevansinya. Generation, Gemini,
FastMCP, dan Gradio belum diimplementasikan.

## Struktur dan environment

Repository menggunakan layout `src`, build backend `uv_build`, Python 3.11,
environment `.venv`, serta `pytest`. Implementasi Milestone 1 (scoring, UCS,
FIFO) dan Milestone 2 (CSP, AC-3, Backtracking) dipertahankan.

Dependensi yang dibutuhkan sudah tersedia di `pyproject.toml` dan `uv.lock`:
ChromaDB 1.5.9 dan sentence-transformers 6.2.0 pada environment verifikasi.
Tidak perlu menjalankan `uv init` atau menambahkan dependensi yang sama.

| File | Tanggung jawab |
|---|---|
| [embeddings.py](../../src/proyek_certan/knowledge/embeddings.py) | Model multilingual, cache model per proses, validasi teks, matriks float32 `(N, D)` ternormalisasi |
| [models.py](../../src/proyek_certan/knowledge/models.py) | Kontrak `KnowledgeChunk`, metadata, dan `SearchResult` |
| [vector_store.py](../../src/proyek_certan/knowledge/vector_store.py) | PersistentClient, collection `certan_knowledge`, cosine distance, upsert, query, dan lifecycle client |
| [retrieval.py](../../src/proyek_certan/knowledge/retrieval.py) | Indexing hasil chunking dan pencarian bahasa alami dengan encoder yang sama |
| [cli.py](../../src/proyek_certan/knowledge/cli.py) | Perintah index/search terpisah dari CLI milestone sebelumnya |
| [sample_knowledge_chunks.json](../../data/sample_knowledge_chunks.json) | Lima contoh chunk insiden sintetis, terpisah dari modul produksi |
| [knowledge_chunks.json](../../data/corpus/processed/knowledge_chunks.json) | Chunk korpus nyata hasil ingestion dan audit 15 TXT |
| [tests/knowledge](../../tests/knowledge) | Pengujian offline dengan Chroma asli dan integrasi model asli |

## Menjalankan dengan uv

Jalankan dari root repository. Environment menggunakan konfigurasi dan lockfile
yang sudah ada:

```bash
uv sync --locked
uv run --locked python -m proyek_certan.knowledge.cli index --input data/sample_knowledge_chunks.json
uv run --locked python -m proyek_certan.knowledge.cli search --query "Kabel LAN putus dan port switch bermasalah" --top-k 3
```

Perintah pertama yang melakukan encoding akan mengunduh model
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` dari Hugging Face.
Model ini menghasilkan **384 dimensi**. Pemakaian berikutnya menggunakan cache
disk; selama satu proses, model yang sama dipakai ulang melalui `lru_cache`.
Model tidak dimuat saat hanya mengimpor modul atau mencari pada collection kosong.

Lokasi default relatif terhadap working directory:

- Database: `.local/chroma` (override `CERTAN_CHROMA_PATH` atau `--db`).
- Cache model: `.cache/models` (override `CERTAN_MODEL_CACHE` atau `--model-cache`).

Gunakan lokasi database yang sama saat indexing dan pencarian. Untuk path khusus:

```bash
uv run --locked python -m proyek_certan.knowledge.cli index --input data/sample_knowledge_chunks.json --db .local/chroma-demo
uv run --locked python -m proyek_certan.knowledge.cli search --db .local/chroma-demo --query "WiFi tersambung tetapi tidak bisa internet" --top-k 3
```

Folder default database/cache diabaikan Git. Jika mengatur lokasi lain, pastikan
folder tersebut juga diabaikan sebelum menambahkan file ke Git. Field `source`
pada data dummy adalah label sumber sintetis, bukan dokumen SOP yang sudah ada.

## Integrasi hasil chunking

`KnowledgeRetriever.index_chunks()` menerima list mapping berikut tanpa perlu
menulis file terlebih dahulu:

```python
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore

chunks = [{
    "chunk_id": "sop-wifi-001",
    "text": "Konten chunk...",
    "metadata": {
        "document_id": "sop-wifi",
        "source": "sop_wifi.pdf",
        "title": "SOP Penanganan WiFi",
        "section": "Troubleshooting",
        "chunk_index": 0,
    },
}]

with VectorStore(".local/chroma-production") as store:
    retriever = KnowledgeRetriever(store)
    retriever.index_chunks(chunks)
    results = retriever.search("WiFi tidak bisa mengakses internet", top_k=3)
    for result in results:
        print(result.chunk_id, result.source, result.similarity)
```

Aturan kontrak:

- `chunk_id` dan `text` adalah string nonkosong. Tim chunking harus menghasilkan
  ID deterministik dan unik lintas dokumen; jangan memakai ID acak setiap indexing.
- `metadata.source` wajib berupa string nonkosong. Field lain boleh ditambahkan
  dengan key string dan nilai scalar `str`, `int`, `float` terbatas, atau `bool`.
  Nilai nested, list, dan `None` ditolak; upstream harus meratakannya terlebih dahulu.
- ID yang sama dalam satu batch ditolak. Indexing ulang pada pemanggilan berikutnya
  memperbarui ID tersebut melalui upsert, termasuk teks, metadata, dan vektornya.
- Batch kosong pada `index_chunks` menjadi no-op, mengembalikan `0`. Teks kosong,
  query kosong, dimensi tidak sesuai, serta vektor nol/nonfinite menghasilkan error.
- Seluruh batch divalidasi sebelum encoding/writing. Batch besar dibagi sesuai
  batas Chroma; penulisan antarbagiannya bukan transaksi atomik.
- Upsert tidak menghapus chunk lama yang tidak lagi ada pada hasil chunking baru.
  Rekonsiliasi versi dokumen dan penghapusan chunk usang perlu disepakati saat integrasi.

Untuk embedding yang sudah dihitung, panggil `VectorStore.upsert(chunks, embeddings)`
dengan matriks `(jumlah_chunk, dimensi)`. Pemanggil bertanggung jawab memakai model
yang sama dengan `store.model_name`. Jalur yang disarankan adalah `index_chunks`,
yang menggunakan encoder yang sama dengan query. Collection menyimpan identitas
model dan menolak pembukaan dengan model berbeda atau konfigurasi selain cosine.
Pergantian model memerlukan database terpisah dan indexing ulang seluruh dokumen.

## Semantik hasil dan threshold

Setiap `SearchResult` memiliki `chunk_id`, `text`, `source`, `metadata`, dan
`similarity`. Hasil diurutkan dari jarak terkecil (similarity tertinggi).

```text
cosine_distance   = 1 - cosine_similarity
cosine_similarity = 1 - cosine_distance
```

Similarity berada pada rentang `[-1, 1]`, bukan probabilitas atau persentase
keyakinan diagnosis. Nilai negatif tetap dipertahankan. Pembulatan numerik di
ujung rentang dibatasi ke `-1`/`1`.

`relevance_threshold=None` berarti tidak memfilter. Contoh konfigurasi percobaan:

```bash
uv run --locked python -m proyek_certan.knowledge.cli search --query "WiFi bermasalah" --top-k 5 --relevance-threshold 0.4
```

**0.4 hanya contoh parameter**, belum dikalibrasi. Filtering dilakukan pada
kandidat top-k sehingga hasil dapat berjumlah kurang dari k atau kosong. Kueri
nonkosong pada collection kosong mengembalikan `[]` tanpa memuat model. `top_k`
dibatasi ke jumlah chunk yang tersedia. Kueri kosong tetap ditolak dengan
`ValueError` (CLI keluar dengan kode 2).

## Pengujian

Pengujian default memakai ChromaDB asli di folder sementara dan encoder stub
untuk memeriksa logika secara deterministik, termasuk similarity `1`, `0`, dan
`-1`. Uji integrasi terpisah memakai model MiniLM yang benar-benar dimuat, bukan
stub. Dua uji integrasi dilewati secara eksplisit jika flag belum diaktifkan.

```bash
uv run --locked python -m pytest -q
```

Jalankan seluruh suite, termasuk model asli, di PowerShell:

```powershell
$env:CERTAN_RUN_MODEL_TESTS = "1"
uv run --locked python -m pytest -q
Remove-Item Env:CERTAN_RUN_MODEL_TESTS
```

Atau hanya integrasi:

```powershell
$env:CERTAN_RUN_MODEL_TESTS = "1"
uv run --locked python -m pytest tests/knowledge/test_integration.py -v
```

Padanan shell POSIX:

```bash
CERTAN_RUN_MODEL_TESTS=1 uv run --locked python -m pytest -q
```

Kegagalan unduhan/model pada uji integrasi menyebabkan **test gagal**, bukan
dianggap lulus atau dilewati secara diam-diam. Uji persistensi juga menulis dari
subproses Python, menunggu proses berakhir, lalu membaca database dari proses lain.

## Hasil verifikasi, 2 November 2026

Perintah berikut benar-benar dijalankan pada environment repository:

| Verifikasi | Hasil |
|---|---|
| `uv sync --locked` | Berhasil; konfigurasi/dependensi yang sudah ada digunakan |
| `uv run --locked python -m pytest -q` | 130 passed, 2 skipped (7.71 detik); flag model belum aktif |
| Dua uji integrasi model asli, flag aktif | 2 passed (174.70 detik termasuk unduhan pertama) |
| Suite akhir, `CERTAN_RUN_MODEL_TESTS=1` | **132 passed (32.41 detik)** setelah penyesuaian API dimensi |
| CLI indexing lima chunk dummy | `{"indexed": 5, "collection_count": 5}` |
| CLI search melalui proses baru | Tiga hasil, metadata lengkap; chunk LAN teratas |

Uji model asli memverifikasi matriks tiga teks `(3, 384)`, dimensi query yang
sama, nilai finite, dan norma L2 mendekati 1. Uji Chroma memverifikasi pembukaan
ulang client dan persistensi setelah proses penulis berakhir. Indexing ulang
lima ID yang sama tetap menghasilkan lima record. Seluruh pengujian Milestone
1 dan 2 termasuk dalam suite akhir di atas.

Contoh output aktual untuk kueri **"Kabel LAN putus dan port switch bermasalah"**:

| Urutan | Chunk ID | Sumber sintetis | Cosine similarity (dibulatkan) |
|---:|---|---|---:|
| 1 | dummy-lan-001 | dummy_sop_lan.txt | 0.767037 |
| 2 | dummy-wifi-001 | dummy_sop_wifi.txt | 0.503568 |
| 3 | dummy-ap-001 | dummy_sop_ap.txt | 0.438947 |

Record pertama dari array JSON hasil CLI:

```json
{
  "chunk_id": "dummy-lan-001",
  "text": "Jika koneksi LAN terputus, periksa kabel Ethernet dan port switch.",
  "source": "dummy_sop_lan.txt",
  "metadata": {
    "chunk_index": 0,
    "document_id": "dummy-lan",
    "section": "Troubleshooting",
    "title": "Contoh SOP LAN (sintetis)",
    "source": "dummy_sop_lan.txt"
  },
  "similarity": 0.7670372724533081
}
```

Angka tersebut merupakan hasil pada model dan data contoh saat verifikasi;
urutan key metadata tidak menjadi bagian dari kontrak. Ini bukan evaluasi
relevansi pada korpus operasional.

## Pekerjaan lanjutan T03

1. Tinjau flag kualitas pada
   [audit korpus](../../evaluation/corpus_chunking.json), lalu tentukan
   dokumen yang layak diindex untuk penggunaan produksi.
2. Ukur panjang chunk terhadap batas token model agar encoding tidak memotong
   konteks penting; ukuran 250 kata dan overlap 40 kata saat ini bersifat eksperimen.
3. Siapkan kueri evaluasi berlabel dan relevansi rujukan dari kasus jaringan kampus.
   Ukur Recall@k/MRR atau metrik retrieval yang disepakati.
4. Kalibrasi top-k dan threshold dari evaluasi tersebut. Lima teks sintetis hanya
   membuktikan pipeline teknis, belum membuktikan kualitas retrieval pada korpus nyata.
5. Sepakati versi korpus/model, indexing ulang, dan rekonsiliasi chunk usang.
6. Lengkapi laporan dan bukti evaluasi sesuai rubrik T03 mata kuliah.
