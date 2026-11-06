# Kandidat riset yang tidak diadopsi

Seluruh kode berikut tetap di luar paket runtime dan dipertahankan pada path
asal agar import, protokol serta SHA-256 tetap berlaku.

| Kandidat | Implementasi | Bukti keputusan |
|---|---|---|
| Bonus intent/metadata v2 | [metadata_intent_candidate.py](../metadata_intent_candidate.py) | [laporan v2](../../docs/milestone-3/directed-improvement-v2.md) |
| Scope guard v3 | [scope_candidate_v3.py](../scope_candidate_v3.py), [CLI riset](../guard_candidate_cli_v3.py) | [keputusan](../quality-v3/decision.json), [analisis v3](../../docs/milestone-3/final-quality-v3.md) |
| Campuran cosine judul v3 | [title_candidate_v3.py](../title_candidate_v3.py) | [final test](../quality-v3/results_final_test.json), CI MRR melintasi nol |

[lock-r2](../quality-v3/lock-r2.json) mengunci konfigurasi sebelum validation
dan final test. [locked-code](../quality-v3/locked-code/) menyimpan enam
snapshot implementasi yang benar-benar diukur. Statusnya tidak dipromosikan
oleh cleanup. [Runner riset](../quality_v3.py) dipertahankan untuk audit;
jangan menjalankan ulang authoring, selection atau pengumpulan final test.
