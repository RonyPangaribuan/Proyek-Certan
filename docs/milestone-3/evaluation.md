# Evaluasi T03 dan batas hasil

## Metode dan bukti

[Benchmark utama](../../evaluation/semantic_retrieval_ground_truth.json) memuat 15 kueri: delapan relevan, dua parafrasa/sinonim, dua ambigu, dan tiga out-of-domain (OOD). Label memiliki document_id target dan alasan berbasis sumber. Relevansi adalah kecocokan topik; tidak menyatakan otoritas kebijakan sumber terhadap kampus.

[Pengukuran aktif](../../evaluation/results/final.json) memakai korpus rekursif 503 chunk dan model multilingual yang sama untuk dokumen/kueri. Ranking dokumen menggunakan maksimum cosine dari 100 kandidat chunk. P@k dan R@k dirata-ratakan pada kueri positif, satu hasil per document_id; MRR dibatasi kandidat yang terambil. Similarity adalah 1 - cosine_distance, bukan probabilitas.

Selain 15 kueri utama, regresi mencakup development 36 kueri, validation 36 dan final_test historis 48. **Semua split tersebut sudah pernah terlihat. Pengukuran baru adalah regresi setelah perubahan splitter, bukan holdout independen baru.** Label, observasi, hasil dan keputusan penelitian lama dipertahankan identik byte; evaluator memeriksa checksumnya dan me-replay baseline lama tanpa retrieval ulang.

## Hasil retrieval aktual

| Pengukuran | Positif + OOD | P@1 | P@3 | R@3 | R@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Legacy 15, regresi aktif | 12 + 3 | 0,7500 | 0,4167 | 0,8750 | 0,9583 | 0,8500 |
| Development, regresi aktif | 18 + 18 | 0,8333 | 0,3333 | 0,9444 | 1,0000 | 0,9028 |
| Validation, regresi aktif | 18 + 18 | 0,8333 | 0,3519 | 1,0000 | 1,0000 | 0,8889 |
| Final_test historis, regresi aktif | 24 + 24 | 0,7083 | 0,3333 | 0,9583 | 0,9583 | 0,8333 |
| Final_test v3, hasil beku asli | 24 + 24 | 0,7083 | 0,3194 | 0,9167 | 0,9583 | 0,8122 |

Perbedaan baris final_test merupakan perbandingan deskriptif pada kueri yang sama setelah splitter berubah. Tidak ada klaim signifikansi atau generalisasi baru. Metrik split berbeda tidak digunakan sebagai perbandingan sebelum/sesudah.

## OOD dan keputusan threshold

Evaluator menguji ambang historis 0,50 dan kalibrasi 0,55. Kalibrasi memakai development saja: grid 0–1 langkah 0,05, minimalkan FAR dengan maksimal satu positif ditolak; seri dipilih berdasarkan FRR lalu threshold lebih rendah. Validation/final_test tidak memilih ulang threshold. **Ambang 0,55 belum diadopsi sebagai kebijakan runtime default.** CLI menyediakan `--threshold` untuk demonstrasi eksplisit.

| Split aktif | Threshold | OOD diterima / seluruh OOD | Positif ditolak / seluruh positif | Precision penolakan | OOD berhasil ditolak |
|---|---:|---:|---:|---:|---:|
| Legacy | 0,50 | 0/3 | 0/12 | 1,0000 | 1,0000 |
| Development | 0,55 | 6/18 | 0/18 | 1,0000 | 0,6667 |
| Validation | 0,55 | 3/18 | 0/18 | 1,0000 | 0,8333 |
| Final_test historis | 0,50 | 18/24 | 1/24 | 0,8571 | 0,2500 |
| Final_test historis | 0,55 | 9/24 | 2/24 | 0,8824 | 0,6250 |

FAR = OOD diterima / seluruh OOD. FRR = positif ditolak / seluruh positif. Precision penolakan = OOD ditolak / semua kueri ditolak; nilainya tidak terdefinisi bila tidak ada penolakan. Precision tinggi saja tidak cukup: sistem juga harus menolak sebagian besar OOD dan menjaga kueri positif.

Tiga OOD legacy yang mudah seluruhnya ditolak, tetapi challenge set masih menunjukkan false acceptance dan false rejection. Karena itu hasil ini belum mendukung klaim penanganan OOD presisi tinggi secara umum. Kandidat guard dan reranking judul lama ditolak berdasarkan eksperimen sebelumnya; keputusan tersebut tetap tersimpan pada [bukti beku](../../evaluation/quality-v3/decision.json).

## Analisis kesalahan

- `wifi_diagnosis`: DOC13 kebijakan berada di atas DOC01 diagnosis (DOC01 rank 5). Kesamaan kata WiFi/kampus mengalahkan perbedaan maksud diagnosis dan kebijakan.
- `packet_loss`: DOC03 DHCP berada di atas DOC07 packet loss. Istilah pemeriksaan klien/jaringan beririsan antarsumber.
- `acceptable_use`: DOC13 berada di atas DOC14 yang menjadi target. Topik kebijakan jaringan saling berdekatan.
- Kueri tanpa jawaban pada korpus, termasuk fakta lokal dan informasi real-time, masih dapat memiliki cosine tinggi.

Perbaikan lanjutan memerlukan penilaian tim/pakar domain dan evaluasi baru yang belum dipakai untuk desain. Label saat ini disusun dari sumber oleh pihak yang mengetahui sistem; belum merupakan validasi manusia independen.

## Sensitivitas chunking

| Profil rekursif | Chunk | Median token | Maksimum token | Di atas 128 token |
|---|---:|---:|---:|---:|
| 96 token / overlap 10 kata (aktif) | 503 | 81 | 96 | 0 |
| 96 token / tanpa overlap | 422 | 81 | 96 | 0 |
| 120 token / overlap 12 kata | 387 | 104 | 120 | 0 |

Semua profil lulus pemeriksaan cakupan urutan kata sumber. Overlap 10 menambah sekitar 19,2% chunk dibanding tanpa overlap pada batas 96 token. Profil 120/12 mengurangi jumlah chunk tetapi hanya menyisakan delapan token terhadap batas model. Perbandingan ini mengukur struktur/biaya, bukan membuktikan akurasi retrieval terbaik. Hanya profil aktif disimpan sebagai korpus final.

## Reproduksi

```bash
uv run --locked python evaluation/benchmarks/final_pipeline.py
uv run --locked python evaluation/benchmarks/final_pipeline.py --live
uv run --locked python -m pytest -q
```

Mode standar tidak memuat model atau membuka database. Mode live memverifikasi reproduksibilitas chunk, model, isi indeks, lalu menjalankan regresi. `--output evaluation/results/nama-baru.json` menyimpan receipt baru dan menolak overwrite. [Evidence manifest](../../evaluation/evidence.json) menyimpan checksum bukti beku, snapshot arsip, inventaris pengurangan, dan hasil verifikasi cleanup.

## Kesesuaian modul dan serahan

| Komponen rubrik | Bukti aktif |
|---|---|
| Korpus/preprocessing 25% | 15 sumber, cleaning terverifikasi, recursive word-aware splitting, alasan size/overlap, sensitivitas dan cakupan kata |
| Embedding/ChromaDB 45% | Sentence-Transformers multilingual, vektor 384 dimensi ternormalisasi, metadata sumber, modul terpisah dan database persisten |
| Retrieval/analisis 30% | Relevan, sinonim, ambigu, OOD; cosine, P/R/MRR, FAR/FRR, precision penolakan dan analisis kegagalan |

Laporan PDF menyajikan metode, hasil aktual, keterbatasan dan referensi sumber. Kode kelompok harus dilengkapi sebelum pengumpulan. Repository mendukung serahan prototipe akademik; hasil ini tidak menjamin seluruh deskriptor nilai 100.
