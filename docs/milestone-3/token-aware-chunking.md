# Eksperimen chunking sesuai batas token model

Model yang dipakai tetap `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(embedding 384 dimensi). Pemeriksaan model lokal menunjukkan
`max_seq_length = 128`, `tokenizer.model_max_length = 128`, dan dua special token
untuk satu input (`<s>` dan `</s>`). Dengan demikian teks isi hanya boleh
memakai paling banyak **126 token**. Penghitungan memakai tokenizer model
dengan `add_special_tokens=True` dan `truncation=False`, sehingga nilai di
laporan sudah mencakup kedua special token. Eksperimen memberi margin 8 atau
32 token di bawah batas 128.

[Chunker](../../src/proyek_certan/corpus/chunking.py) tetap memisahkan section,
kemudian mengutamakan batas baris/paragraf dan kata. Batas token diterapkan di
batas kata melalui pencarian ujung terpanjang yang muat; overlap dihitung dalam
kata dan hanya berlaku di dalam section. Apabila overlap membuat chunk berikutnya
tidak maju, overlap dikurangi untuk menjaga cakupan. Kata tunggal yang melebihi
batas akan menghasilkan error eksplisit, bukan dipotong diam-diam. Pemeriksaan
rekonstruksi urutan kata pada semua section berhasil untuk kedua konfigurasi.
Normalisasi whitespace mengikuti pipeline ingestion sebelumnya; tidak ada
perubahan substansi 15 teks sumber.

| Profil | Batas total token | Overlap kata | Chunk | Token min / median / maks | Durasi indexing |
|---|---:|---:|---:|---|---:|
| Baseline, 250 kata / 40 overlap | 128 model | 40 | 130 | 30 / tidak dicatat / 675 | 51,673 dtk (index awal) |
| `t120_w12` | 120 | 12 | 374 | 20 / 109 / 120 | 53,199 dtk |
| `t96_w10` | 96 | 10 | 484 | 22 / 84,5 / 96 | 59,513 dtk |

Baseline memiliki 115/130 chunk di atas 128 token. Kedua profil baru memiliki
**0 chunk di atas 128 token**, ID unik, cakupan DOC01–DOC15, dan teks serta
metadata tersimpan sama dengan JSON input. Database persisten baru dibuka dari
proses Python terpisah dan berisi masing-masing 374 dan 484 record. Baseline
tetap berisi 130 record. Distribusi token lengkap, jumlah per dokumen, checksum
input, dan statistik lain ada di
[laporan perbandingan](../../evaluation/token_chunking_comparison.json).

| Kueri | Baseline top-1 | `t120_w12` top-1 | `t96_w10` top-1 |
|---|---|---|---|
| WiFi | DOC13 (0,589) | DOC13 (0,748) | DOC13 (0,737) |
| DNS | DOC02 (0,676) | DOC02 (0,685) | DOC02 (0,709) |
| DHCP | DOC03 (0,744) | DOC03 (0,732) | DOC03 (0,747) |
| VLAN | DOC06 (0,760) | DOC06 (0,755) | DOC06 (0,782) |
| Eskalasi P1 | DOC09 (0,509) | DOC10 (0,639) | DOC10 (0,555) |

Ini adalah smoke test lima kueri yang sama, `top_k=3`, tanpa label relevansi.
Skor cosine similarity antarprofil bukan ukuran akurasi yang dapat langsung
dibandingkan karena batas chunk mengubah teks yang di-embed. DNS, DHCP, dan
VLAN tetap mengarah ke dokumen top-1 yang sesuai topik. Kueri WiFi masih
mengutamakan kebijakan jaringan DOC13, bukan panduan WiFi DOC01, sehingga
perlu evaluasi berlabel. Kueri eskalasi berpindah ke DOC10 yang masih DRAFT.
Hasil lengkap, teks chunk, judul, section, URL, dan similarity ada di
[hasil 120 token](../../evaluation/real_corpus_search_t120_w12.json) dan
[hasil 96 token](../../evaluation/real_corpus_search_t96_w10.json).

Profil 120 token memakai lebih sedikit chunk, sehingga penyimpanan dan
pencarian lebih hemat serta konteks tiap hasil lebih panjang. Profil 96 token
memberi margin truncation lebih besar dan potongan lebih terfokus, dengan
tambahan 110 record dan lebih banyak batas antarchunk. Keduanya layak sebagai
dasar evaluasi retrieval T03; pilihan final membutuhkan label relevansi dan
review isi. DOC06, DOC09, DOC10, DOC11, dan DOC13 tetap memiliki flag review.
Status `DRAFT` pada DOC09/10 tetap ada di metadata. Eksperimen ini belum
menyetujui indeks untuk produksi.

Jalankan ulang dari root repository dengan environment `uv` yang ada:

```powershell
uv run --frozen --no-sync python -m proyek_certan.corpus.token_experiment
```

Perintah membuat [chunk 120 token](../../data/corpus/processed/knowledge_chunks_t120_w12.json)
dan [chunk 96 token](../../data/corpus/processed/knowledge_chunks_t96_w10.json)
serta dua database di `.local/`. Database eksperimen harus belum ada agar
hasil tidak tercampur dengan run lama; untuk run ulang, pakai checkout bersih
atau path eksperimen baru. Baseline chunk dan database tidak ditimpa.

Validasi akhir: suite penuh dengan model nyata menghasilkan **172 passed**;
`uv lock --check` dan `git diff --check` lulus. Tidak ada commit atau push.
