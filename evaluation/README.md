# Evaluasi CERTAN

Untuk pipeline aktif, mulai dari [panduan M3](../docs/milestone-3/README.md) dan [evaluator resmi](benchmarks/README.md). Hanya profil `v3_t96_w10` dari [manifest final](../data/corpus/final/manifest.json) yang aktif.

| Kelompok | Pintu masuk | Status |
|---|---|---|
| Final | [benchmarks](benchmarks/README.md) | Audit final, replay metrik tersimpan, regresi legacy opsional |
| Hasil | [results](results/README.md) | Receipt cleanup dan navigasi hasil beku |
| Rejected experiments | [experiments](experiments/README.md) | Intent, scope guard dan title reranking tidak diadopsi |
| Historical evidence | [archive](archive/README.md) | Baseline v1/v2/v3, label, protokol dan snapshot |
| Generated | `.local/`, `.cache/` | Indeks, model dan render lokal; diabaikan Git |

```bash
uv run --locked python evaluation/benchmarks/final_pipeline.py
uv run --locked python evaluation/benchmarks/final_pipeline.py --live
```

Perintah pertama memverifikasi hash, tautan lokal dan aritmetika hasil beku. `--live` menambahkan pemeriksaan token/model/indeks dan regresi 15 kueri legacy. Tidak ada authoring label, threshold selection atau pengulangan retrieval validation/final test.

Berkas lama pada root direktori ini serta [quality-v3](quality-v3/) tetap di path aslinya. Banyak import menggunakan root `evaluation` dan `Path(__file__).parents[1]`; protokol serta laporan juga membekukan path/hash. Pemisahan dilakukan melalui indeks navigasi agar integritas penelitian tetap terjamin. Lokasi lama tidak menyatakan status aktif.

Jangan menjalankan ulang entrypoint authoring/selection/create-once, termasuk `prepare_*`, `build_reviewed_*`, `quality_v3.py` selection/collect/report dan `final_verify_quality_v3.py`. Skrip benchmark lama juga dapat menimpa laporan historis melalui entrypoint-nya. Gunakan evaluator resmi di atas untuk verifikasi baca-saja; simpan receipt baru hanya pada [results](results/).

Angka tes, jumlah chunk dan path database dalam laporan lama adalah keadaan pada tahap riset masing-masing. Acuan penggunaan sekarang adalah manifest final; protokol dan hasil lama tidak ditulis ulang agar terlihat seperti konfigurasi aktif.
