# Hasil final dan indeks hasil penelitian

Hasil ilmiah historis tetap pada lokasi beku; tautan berikut merupakan indeks,
bukan salinan atau penggantian hasil.

| Kelompok | Hasil | Interpretasi |
|---|---|---|
| Cleanup | [laporan](../../docs/milestone-3/repository-cleanup.md) | Verifikasi organisasi dan jalur final; tidak mengubah metrik ilmiah |
| Legacy 15 kueri | [benchmark v1](../semantic_retrieval_benchmark.json) | Dua profil lama; 12 relevan dan 3 OOD |
| Studi 75 kueri | [hasil v2](../retrieval_study_results_v2.json) | Baseline, review, ablation dan intent; split lama tetap |
| Development v3 | [hasil awal](../quality-v3/results_development.json), [r2](../quality-v3/results_development_r2.json) | Perbaikan parser hanya pada development, dijelaskan amendment |
| Validation v3 | [hasil](../quality-v3/results_validation.json) | 18 relevan + 18 OOD, tidak digabung dengan final test |
| Final test v3 | [hasil](../quality-v3/results_final_test.json) | 24 relevan + 24 OOD, pengukuran create-once |
| Keputusan | [decision](../quality-v3/decision.json) | Guardrail dan reranking judul ditolak |
| Regresi 75 kueri | [perbandingan tersimpan](../quality-v3/historical_75_comparison.json) | Tidak digunakan untuk pemilihan strategi |

Receipt baru pada direktori ini hanya mencatat verifikasi cleanup. Metrik
legacy yang dijalankan kembali bukan pengukuran ulang validation/final test.
