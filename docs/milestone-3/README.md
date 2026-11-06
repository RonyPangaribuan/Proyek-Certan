# Milestone 3: panduan penggunaan

Deliverable T03 adalah korpus bersih, pipeline ingestion/chunking, indeks ChromaDB persisten, dan laporan benchmark. Jalur final memakai 15 dokumen dan profil tunggal `recursive_t96_w10` (503 chunk). [Pipeline](pipeline.md) menjelaskan sumber dan metode; [evaluasi](evaluation.md) menjelaskan bukti dan keterbatasan.

## Jalankan dari root repository

```bash
uv sync --locked
uv run --locked python -m proyek_certan.knowledge.final_cli verify
uv run --locked python -m proyek_certan.knowledge.final_cli build
uv run --locked python -m proyek_certan.knowledge.final_cli index
uv run --locked python -m proyek_certan.knowledge.final_cli verify --index
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Nama domain gagal di-resolve. Bagaimana memeriksa DNS server dan klien?" --document-level --top-k 5
```

`verify` memeriksa hash sumber dan teks aktif, metadata, jumlah dan cakupan dokumen. `build` membentuk chunk deterministik dari TXT final dan memverifikasi kesamaan byte, tanpa menulis korpus. Opsi `build --output .local/chunks-rebuilt.json` menulis salinan baru dan menolak overwrite; direktori tujuan harus sudah ada.

`index` membangun `.local/chroma-final-recursive/`, kemudian memeriksa ID, teks, metadata dan vektor. Jalankan `verify --index` dalam proses berikutnya untuk menunjukkan persistensi. Indexing ulang tidak menambah duplikat. Indeks lama/campuran ditolak; `--db` memilih lokasi terisolasi tanpa menghapus database.

Default `search` mengembalikan chunk. `--document-level` memilih cosine tertinggi per dokumen dari 100 kandidat chunk. Hasil menyertakan sumber, bagian, metadata dan similarity; similarity bukan probabilitas relevansi.

## Demonstrasi kueri

| Jenis | Contoh |
|---|---|
| Relevan | Nama domain gagal di-resolve; bagaimana memeriksa DNS server dan klien? |
| Sinonim/parafrasa | Laptop sering terputus dari jaringan nirkabel di satu SSID. Apa yang dicek pada klien dan AP? |
| Ambigu | Gangguan layanan perlu dicatat, diprioritaskan, lalu ditutup. Apa alur tiket insiden? |
| Out-of-domain | Berapa harga nasi goreng dan jam buka kantin kampus besok? |

Untuk demonstrasi mekanisme threshold secara eksplisit:

```bash
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Berapa harga nasi goreng di kantin?" --document-level --threshold 0.5
```

Threshold adalah opsi eksperimen, tidak aktif secara default dan tidak dijamin optimal. Output `LOW_CONFIDENCE` berarti kandidat teratas di bawah threshold tersebut. Kandidat guard dan reranking judul lama tidak diadopsi.

## Evaluasi

```bash
uv run --locked python evaluation/benchmarks/final_pipeline.py
uv run --locked python evaluation/benchmarks/final_pipeline.py --live
```

Mode standar memeriksa bukti beku tanpa memuat model atau membuka database. Mode live membutuhkan indeks serta cache model dan menjalankan regresi pada split yang sudah pernah dilihat. Untuk menyimpan pengukuran baru, gunakan `--output evaluation/results/nama-baru.json`; berkas yang sudah ada ditolak.

## Berkas yang ditunjukkan kepada dosen

1. [Manifest final](../../data/corpus/final/manifest.json): daftar 15 sumber, hash, hak/status sumber dan konfigurasi.
2. [Ekstraksi](../../src/proyek_certan/corpus/prepare.py), [normalisasi](../../src/proyek_certan/corpus/cleaning.py), [chunking](../../src/proyek_certan/corpus/chunking.py) dan [ingestion](../../src/proyek_certan/corpus/ingestion.py).
3. [Embedding](../../src/proyek_certan/knowledge/embeddings.py), [vector store](../../src/proyek_certan/knowledge/vector_store.py) dan [retrieval](../../src/proyek_certan/knowledge/retrieval.py).
4. [Evaluator](../../evaluation/benchmarks/final_pipeline.py) dan [bukti/checksum](../../evaluation/evidence.json).

## Serahan

[Laporan PDF draft](../../output/pdf/CERTAN-Tugas03-draft.pdf) memuat metode, hasil pengujian aktual dan keterbatasan. Kode kelompok dan pemeriksaan akhir tim perlu dilengkapi sebelum pengumpulan. Repository tidak menyatakan seluruh deskriptor nilai 100 telah terpenuhi; domain lokal, DRAFT, dan akurasi OOD tetap memiliki keterbatasan. Pengambilan jawaban dengan LLM/RAG merupakan tahap selanjutnya.
