# Pipeline dan provenance korpus

## Cakupan domain

CERTAN memakai 15 sumber untuk diagnosis jaringan, pengelolaan insiden dan kebijakan penggunaan jaringan. Sumber ini relevan terhadap rujukan penanganan insiden, tetapi belum membuktikan representativitas insiden nyata kampus. Terdapat 13 dokumen berbahasa Inggris dan dua Indonesia; pemetaan sumber, URL, publisher, hak penggunaan, status dan hash ada dalam [manifest final](../../data/corpus/final/manifest.json).

- DOC01–DOC08: WiFi, DNS, DHCP, TCP/IP, VLAN/switch, packet loss dan autentikasi.
- DOC09–DOC12: service desk, penanganan insiden, incident management dan keamanan.
- DOC13–DOC15: administrasi, acceptable use dan pengelolaan jaringan.

DOC09/10 tetap DRAFT. Tabel dan diagram DOC11 belum seluruhnya menjadi teks terstruktur yang aman. Retrieval dari dokumen universitas lain bukan pengesahan kebijakan lokal.

## 1. Akuisisi dan ekstraksi

Seluruh [15 PDF asli](../../data/corpus/raw/) dipertahankan. Dua sumber memakai teks PDF native (DOC11/13); 13 PDF tidak menyediakan ekstraksi yang memadai sehingga teks diturunkan dari halaman HTML resmi yang tercatat. Snapshot hasil review disimpan sebagai 15 TXT pada [korpus final](../../data/corpus/final/).

Pembangunan ulang final menggunakan snapshot TXT terverifikasi, sehingga tidak bergantung pada perubahan situs atau izin akses jaringan. Ini bukan klaim bahwa semua teks dapat diekstrak ulang dari PDF saja. Riwayat ekstraksi dan koreksi asli tersedia pada tag arsip.

Untuk membuat kandidat ekstraksi lokal baru tanpa menimpa hasil lama:

```bash
uv run --locked python -m proyek_certan.corpus.prepare --input data/corpus/raw/DOC13_Network_Administration.pdf --kind pdf --title "University Network Administration" --output .local/review-candidate.txt
```

`--kind html` menerima HTML lokal dan `--publisher` memilih aturan isi utama. `--kind text` menormalisasi teks. Kandidat harus ditinjau sebelum diadopsi; perintah ini tidak mengubah manifest atau korpus aktif. Halaman PDF tanpa teks dan HTML pendek/challenge ditolak.

## 2. Cleaning dan review

[Normalisasi](../../src/proyek_certan/corpus/cleaning.py) menyamakan newline/Unicode, membuang karakter tak terlihat dan merapikan whitespace. Heading, urutan langkah, perintah dan kata substantif tetap dijaga. Penghapusan running header/folio dan reflow spesifik sumber telah direview pada tahap penelitian; snapshot final mempertahankan hasil tersebut tanpa pembersihan agresif ulang.

Status DRAFT, peringatan sumber dan catatan layout dipertahankan. Review sumber meliputi struktur, istilah teknis, urutan langkah dan bagian yang berisiko kehilangan makna. Tidak ada isi tabel atau diagram yang dikarang.

## 3. Recursive word-aware chunking

[Chunking](../../src/proyek_certan/corpus/chunking.py) mengenali heading/pertanyaan, mengelompokkan bagian pendek, lalu mencari jendela kata yang muat dalam anggaran tokenizer. Untuk bagian yang panjang, fungsi rekursif mencoba batas paragraf, baris, kalimat, lalu batas kata. Batas struktur dipilih jika mengisi lebih dari setengah jendela agar tidak menghasilkan terlalu banyak fragmen pendek.

| Parameter aktif | Nilai |
|---|---|
| Profil | `recursive_t96_w10` |
| Batas chunk | 96 token model, termasuk special tokens |
| Overlap yang diminta | 10 kata, dibatasi ruang token dan kemajuan chunk |
| Batas sekunder | 250 kata sebelum pengukuran tokenizer |
| Batas model | 128 token |
| Hasil | 503 chunk; panjang 19–96 token, median 81 |

96 token menyisakan margin 32 terhadap batas model sehingga encoder tidak perlu memotong isi. Overlap menjaga konteks di perbatasan dengan biaya penambahan chunk. Overlap dimulai ulang pada kelompok bagian baru dan bisa diperkecil jika anggaran tidak cukup. Parameter ini merupakan pilihan prototipe yang dijustifikasi oleh batas model, konteks dan bukti sensitivitas; tidak diklaim optimum universal.

[Ingestion](../../src/proyek_certan/corpus/ingestion.py) memverifikasi hash TXT/PDF, menjalankan normalisasi, chunking dan pemeriksaan cakupan urutan kata. Seluruh chunk harus muat dalam batas. Profil 96/0 dan 120/12 dibandingkan dalam memori oleh evaluator untuk sensitivitas jumlah/panjang chunk, tanpa menyimpan korpus alternatif aktif.

## 4. Embedding dan metadata

Model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` dipilih karena kueri Indonesia dan sebagian besar sumber Inggris. [Encoder](../../src/proyek_certan/knowledge/embeddings.py) dimuat lazy, dipakai ulang dan menghasilkan float32 384 dimensi dengan normalisasi L2. Dokumen dan kueri wajib memakai model yang sama. Pemilihan ini beralasan untuk prototipe bilingual, tanpa klaim model terbaik.

Metadata mencakup document_id, sumber, judul, bagian, chunk_index, bahasa, publisher, jenis dokumen, URL, metode ekstraksi, hash PDF/TXT, path TXT aktif, versi/profil, review note dan status/hak sumber jika tersedia. Halaman diberikan hanya jika kata chunk cocok persis dan unik pada PDF native; tidak ada perkiraan halaman untuk sumber HTML.

## 5. Persistent ChromaDB dan retrieval

[Vector store](../../src/proyek_certan/knowledge/vector_store.py) memakai PersistentClient, collection `certan_knowledge`, explicit embeddings dan HNSW cosine. Upsert memperbarui ID tanpa menduplikasi; CLI menolak indeks stale/campuran sebelum encoding. Membuka kembali database dalam proses baru menguji persistensi.

[Retrieval](../../src/proyek_certan/knowledge/retrieval.py) memakai `similarity = 1 - cosine_distance`. Pencarian dokumen memilih cosine tertinggi per document_id dari 100 kandidat chunk; hasil bisa tidak mencakup semua dokumen. Metadata disiapkan untuk pengembangan filtering/hybrid search, sedangkan ranking aktif tetap dense cosine.

## Reproduksi dan arsip

```bash
uv run --locked python -m proyek_certan.knowledge.final_cli build
uv run --locked python -m proyek_certan.knowledge.final_cli index
uv run --locked python -m proyek_certan.knowledge.final_cli verify --index
```

Hanya manifest, PDF asli dan TXT/chunk final diperlukan runtime. Field path historis di dalam provenance adalah catatan sumber yang dapat dilihat pada tag `archive/m3-before-minimal-cleanup-20261106`; field tersebut tidak dibaca sebagai file runtime.

Snapshot tag memuat seluruh korpus v1/v2/v3, generator label, kandidat yang ditolak, laporan dan tes penelitian. [Inventaris cleanup](../../evaluation/evidence.json) mencatat path yang dikeluarkan. [README proyek](../../README.md#struktur-dan-arsip) menjelaskan cara membuka arsip.
