# T03: benchmark semantic retrieval pada korpus nyata

> Baseline historis tetap: angka di bawah merujuk korpus v1 dan 15 kueri lama.
> Audit sumber, korpus review terpisah, 60 kueri tambahan, split kalibrasi/evaluasi,
> dan keputusan eksperimen tersedia pada [laporan peningkatan v2](./directed-improvement-v2.md).
> Benchmark lama tidak ditimpa oleh evaluasi baru.

## Data dan metode

Benchmark ini memakai 15 kueri Indonesia: 12 kueri bertopik korpus (relevan,
parafrasa, ambigu) dan 3 kueri out-of-domain (OOD). [Label dan alasan](../../evaluation/semantic_retrieval_ground_truth.json)
ditulis dari teks sumber di `data/corpus/processed/` sebelum benchmark dijalankan,
tanpa melihat ranking dari run ini. Unit relevansi adalah **dokumen**, karena ID
chunk berubah saat ukuran chunk berubah. Label kosong pada OOD berarti sistem
seharusnya menolak hasil. Label mengukur kesesuaian topik, bukan otoritas SOP
untuk kampus CERTAN.

Kedua database Chroma persisten yang telah diindeks dibaca ulang dengan model
asli `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Kueri sama
persis untuk kedua profil. Hasil 100 chunk teratas per kueri disimpan beserta
ID, dokumen, section, similarity, dan flag review dalam
[hasil benchmark](../../evaluation/semantic_retrieval_benchmark.json). Ranking
dokumen diperoleh dari kemunculan pertama tiap `document_id` pada ranking chunk.
Setiap kueri memiliki setidaknya lima dokumen berbeda dalam 100 chunk tersebut.
Recall@k = dokumen relevan yang ditemukan / jumlah dokumen relevan;
Precision@k = dokumen relevan di k posisi pertama / k; MRR = kebalikan rank
dokumen relevan pertama (dibatasi 100 hasil chunk). Metrik di bawah adalah
rata-rata makro atas 12 kueri dengan label relevan. Recall dan MRR tidak
didefinisikan untuk OOD; OOD dinilai terpisah melalui penerimaan top-1.

## Hasil aktual

| Ukuran | `t120_w12` | `t96_w10` |
|---|---:|---:|
| Chunk tersimpan | 374 | 484 |
| Durasi indexing sebelumnya | 53,199 detik | 59,513 detik |
| Recall@1 | 0,4861 | 0,4861 |
| Recall@3 | 0,7917 | **0,8750** |
| Recall@5 | 0,9167 | 0,9167 |
| Precision@1 | 0,6667 | 0,6667 |
| Precision@3 | 0,3889 | **0,4167** |
| Precision@5 | 0,2667 | 0,2667 |
| MRR | 0,7847 | **0,8056** |
| Top-1 tepat, dari 12 kueri relevan | 8 | 8 |

`t96_w10` menambah 110 chunk (29,4%) dan durasi indexing 6,314 detik (11,9%)
dibanding `t120_w12`, pada run indexing terdahulu. Waktu tersebut pengukuran
sekali, bukan benchmark latensi yang diulang. Kedua profil berada di bawah batas
128 token model dan mencakup 15 dokumen. `t96_w10` memberi Recall@3 lebih baik:
parafrasa WiFi menemukan DOC-01 di rank dokumen 2, dibanding rank 4 pada
`t120_w12`; DHCP menemukan DOC-03 dan DOC-04 dalam tiga dokumen pertama,
dibanding hanya DOC-03. Sebaliknya, pada kueri eskalasi DOC-09 turun dari rank
2 ke rank 4 pada `t96_w10`. Kedua profil tetap melewatkan DOC-01 dalam Top-5
dokumen untuk kueri WiFi awal, dan sama-sama menempatkan DOC-13 di Top-1 pada
kueri penggunaan jaringan umum yang berlabel DOC-14. Dengan hanya 12 kueri
positif, selisih ini belum membuktikan keunggulan statistik umum.

## Similarity, threshold, dan kegagalan WiFi

Skor adalah `1 - cosine_distance`, bukan probabilitas kebenaran. Pada tiga OOD,
rentang skor Top-1 adalah 0,2634–0,4668 (`t120_w12`) dan 0,3011–0,4494
(`t96_w10`). Tanpa filter, semua OOD mendapat hasil, semuanya DOC-09.
Threshold Top-1 `0,4` masih menerima kueri UKT OOD pada kedua profil.
Threshold `0,5` menolak ketiga OOD dan menerima 12/12 kueri positif pada kedua
profil. Namun, dari 12 yang diterima hanya 8 memiliki dokumen Top-1 relevan:
threshold itu **tidak** memisahkan kecocokan topik yang salah. Pada `0,6`,
profil 120 menolak satu kueri positif dan profil 96 menolak dua. Grid dan ID
kueri yang ditolak ada dalam JSON hasil. `0,5` hanya kandidat threshold untuk
eksperimen berikutnya; tiga contoh OOD terlalu sedikit untuk kalibrasi produksi.

Kueri diagnosis WiFi menghasilkan DOC-13 Top-1 dengan similarity **0,7479**
(`t120_w12`) atau **0,7374** (`t96_w10`). DOC-01 baru muncul di rank dokumen
**6** pada keduanya. DOC-13 memuat istilah Wi-Fi, University Network, Internet,
dan access point, tetapi isinya kebijakan pemasangan dan administrasi perangkat.
DOC-01 berisi langkah identifikasi masalah SSID/AP dan klien. Kecocokan istilah
permukaan dan banyaknya chunk DOC-13 di posisi awal membuat retrieval tanpa
reranking atau pembatasan intent memilih kebijakan untuk pertanyaan diagnosis.
Menaikkan threshold tidak memperbaikinya: skor dokumen salah justru tinggi.
Ini membatasi penggunaan hasil Top-1 sebagai dasar rekomendasi penanganan.

## Status DRAFT dan keputusan

DOC-09 (service desk) dan DOC-10 (insiden operasional) masih berstatus **DRAFT**
di sumber, dan status itu dipertahankan pada metadata chunk. Keduanya relevan
secara topik untuk kueri eskalasi dan alur insiden, sehingga dihitung dalam
metrik retrieval. Angka Recall/MRR tersebut **tidak** berarti prosedur, target
SLA, atau tenggat pada DRAFT telah disahkan. Beberapa bagian bahkan masih
memuat placeholder `[Diisi institusi]`. Semua Top-1 OOD yang keliru mengarah
ke DOC-09; karena itu DRAFT perlu pemeriksaan otoritas terpisah sebelum suatu
hasil boleh dipakai untuk jawaban operasional. Dokumen DOC-06, DOC-11, dan
DOC-13 juga masih berflag `review_required` menurut audit sebelumnya.

Untuk tahap evaluasi T03, pilih **`t96_w10`** sebagai konfigurasi retrieval
eksperimen: Recall@3 dan MRR lebih tinggi, dengan biaya 110 chunk dan 6,314
detik indexing tambahan yang terukur. Pilihan ini belum menyetujui deployment
operasional. Sebelum itu, evaluasi intent diagnosis versus kebijakan,
reranking/diversifikasi dokumen, perluasan kueri OOD dan kueri nyata, serta
review otoritas DRAFT dan dokumen berflag masih diperlukan. Pilihan ini
berdasarkan relevansi berlabel dan biaya, bukan perbandingan skor similarity
antarchunk yang panjangnya berbeda.

## Reproduksi dan verifikasi

Jalankan dari root repository setelah kedua indeks persisten tersedia:

```powershell
uv run --frozen --no-sync python evaluation/benchmark_semantic_retrieval.py
uv run --frozen --no-sync python -m pytest tests/knowledge/test_semantic_benchmark_metrics.py tests/knowledge/test_real_corpus_pipeline.py tests/corpus/test_token_chunking.py -q
```

Run benchmark memakai model asli dan memverifikasi jumlah indeks serta SHA-256
file chunk. Pengujian terkait menghasilkan **7 passed**. Tidak ada indexing ulang
atau perubahan modul Milestone 1 dan 2. Suite penuh tanpa flag integrasi model
menghasilkan **172 passed, 2 skipped**; benchmark sendiri tetap memakai model
embedding asli.
