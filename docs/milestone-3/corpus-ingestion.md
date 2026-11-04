# Audit, ingestion, dan chunking korpus Milestone 3

[ingestion.py](../../src/proyek_certan/corpus/ingestion.py) membaca 15 dokumen
dari [corpus_manifest.json](../../data/corpus/corpus_manifest.json), bukan daftar
filename di kode. Setiap TXT harus berada di
[processed/](../../data/corpus/processed/) dan hash SHA-256 serta panjangnya
harus cocok dengan [laporan persiapan](../../evaluation/corpus_processing.json).
Kegagalan integritas menghentikan ekspor. File TXT dan PDF sumber tidak diubah.

Jalankan dari root repository memakai environment `uv` yang ada:

```powershell
uv run --frozen --no-sync python -m proyek_certan.corpus.ingestion
```

Hasilnya adalah [knowledge_chunks.json](../../data/corpus/processed/knowledge_chunks.json)
berupa array JSON yang langsung sesuai kontrak `KnowledgeChunk` dan
`KnowledgeRetriever.index_chunks()`. Audit dan statistik per dokumen tersimpan
di [corpus_chunking.json](../../evaluation/corpus_chunking.json).
Tahap ini hanya menyiapkan data; ChromaDB dan model embedding tidak dijalankan.

## Metode

[cleaning.py](../../src/proyek_certan/corpus/cleaning.py) menormalkan Unicode
NFC, line ending, spasi non-breaking, whitespace akhir baris, dan baris kosong
berlebih. Kata, heading, urutan langkah, perintah teknis, dan baris kode tidak
diterjemahkan atau ditambah. Teks asal tetap tersimpan dalam TXT.

[chunking.py](../../src/proyek_certan/corpus/chunking.py) mengenali heading
Markdown, judul kebijakan bernomor/angka Romawi, dan pertanyaan FAQ. Section
pendek yang berdekatan dikelompokkan agar chunk tidak hanya berisi judul.
Di dalam kelompok, batas baris/paragraf dipilih sebelum pemotongan berdasarkan
kata. Ukuran eksperimen adalah **250 kata** dan overlap **40 kata**. Kata
dihitung sebagai token non-whitespace, bukan token model embedding. Overlap
berlaku antar-chunk dalam kelompok section yang sama dan dimulai ulang pada
batas kelompok. Karena itu tidak setiap pasangan chunk memiliki overlap.

Setiap chunk memiliki ID deterministik `DOCxx-0000`, `text`, serta metadata
scalar `document_id`, `source` (filename PDF), `title`, `section`,
`chunk_index`, dan `source_url`. ID tetap sama untuk input dan parameter
yang sama. Perubahan ukuran chunk atau isi dokumen dapat menggeser indeks;
sebelum reindexing ke database lama, chunk usang perlu direkonsiliasi.

## Hasil korpus nyata

| Metrik | Hasil |
|---|---:|
| Dokumen TXT tervalidasi | 15 |
| Kata sumber setelah cleaning | 20.632 |
| Total chunk | 130 |
| Minimum / median / rerata / maksimum kata per chunk | 18 / 169 / 169,17 / 250 |
| Chunk 1–49 / 50–99 / 100–149 / 150–199 / 200–250 kata | 6 / 13 / 34 / 27 / 50 |
| Dokumen dengan flag kualitas | 9 |
| Dokumen perlu review isi sebelum indexing produksi | 5 |

Rincian jumlah chunk dan flag setiap dokumen ada di
[laporan audit](../../evaluation/corpus_chunking.json). Audit otomatis
memastikan file lengkap menurut manifest dan laporan pemrosesan, UTF-8 dapat
dibaca, heading/section/langkah dapat dikenali, dan tidak ada teks kosong.
Audit ini tidak membuktikan kesetaraan semantik terhadap seluruh isi visual PDF
atau halaman web yang mungkin telah berubah.

Temuan yang perlu ditinjau:

- DOC-06: satu baris teks hasil HTML merapatkan beberapa perintah
  `ovs-vsctl` dengan prosa. Urutan dan kata dipertahankan; lihat sumber resmi
  ketika menilai instruksi yang akan dipakai.
- DOC-11 dan DOC-13: hasil `pypdf` masih memiliki baris yang terputus oleh
  tata letak halaman. DOC-11 juga mengandung nomor halaman/daftar isi.
  Potensi fragmen ini tidak dihapus otomatis karena dapat menghilangkan
  informasi kebijakan yang sah.
- DOC-09 dan DOC-10: halaman sumber berstatus **DRAFT**. Chunk dapat
  digunakan untuk eksperimen, tetapi jangan diperlakukan sebagai SOP yang
  sudah disahkan.
- Lima dokumen memiliki baris sumber panjang; flag ini informasional dan
  menunjukkan paragraf HTML panjang yang dipertahankan.

Pengujian:

```powershell
uv run --frozen --no-sync python -m pytest tests/corpus -q
uv run --frozen --no-sync python -m pytest -q
```

Hasil aktual: **164 passed, 2 skipped** pada suite penuh. Seluruh 130 chunk
hasil nyata lulus validasi `KnowledgeChunk`; rekonstruksi urutan kata dari
setiap kelompok section cocok dengan 15 TXT yang telah dinormalisasi.
Overlap 40 kata pada pasangan chunk dalam kelompok yang sama juga terverifikasi.
