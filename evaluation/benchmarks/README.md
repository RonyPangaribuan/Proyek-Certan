# Evaluator resmi korpus final

[final_pipeline.py](final_pipeline.py) adalah satu entrypoint evaluasi aktif.
Ia membaca [manifest final](../../data/corpus/final/manifest.json) dan
implementasi retrieval yang sama dengan CLI resmi.

```bash
uv run --locked python evaluation/benchmarks/final_pipeline.py
uv run --locked python evaluation/benchmarks/final_pipeline.py --live
```

Pemeriksaan standar mencakup seluruh berkas awal, PDF, baseline beku v2/v3,
enam snapshot kode, label, keputusan penolakan kandidat, replay aritmetika
development/validation/final test, tautan Markdown lokal dan pola kredensial.
`--live` memerlukan indeks final dan model: memeriksa panjang token aktual,
dimensi/norma vektor, isi persisten, serta mengulang **15 kueri legacy**.
Recall/Precision dihitung pada dokumen unik untuk k=1/3/5, MRR pada kandidat
100 chunk, dan threshold 0,5 hanya diagnosis historis.

Validation/final-test retrieval dan pemilihan threshold/kandidat tidak
diulang. Hasil final test yang sudah dibekukan diverifikasi melalui observasi
tersimpan. Tidak ada perubahan label agar regresi terlihat berhasil.

Opsional simpan receipt baru dengan `--output evaluation/results/nama-baru.json`.
Output hanya boleh berada langsung di results dan tidak boleh menimpa berkas.
Tanpa opsi output, pemeriksaan hanya mencetak ringkasan. [Hasil cleanup](../results/README.md)
memisahkan regresi terbaru dari hasil ilmiah lama.
