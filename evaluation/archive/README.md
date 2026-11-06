# Indeks bukti historis dan kompatibilitas path

Tidak ada pemindahan fisik artefak lama. Pemetaan kompatibilitas adalah
**path historis → path historis yang sama**. Protokol mengunci bytes/hash dan
skrip saling mengimpor dari root evaluation, memakai parent path tetap atau
dirujuk langsung oleh tes. Indeks ini memisahkan status riset tanpa merusak
dependensi tersebut.

- [Inventaris sebelum perubahan](cleanup-baseline.json): 231 berkas Git, SHA-256 per berkas, 633 import, 183 literal path, 246 tautan lokal dan ringkasan generated lokal. Direkam saat working tree bersih pada commit `7d27d33`.
- Sumber/persiapan: [validasi PDF](../pdf_validation.json), [pemrosesan](../corpus_processing.json), [chunking awal](../corpus_chunking.json), [eksperimen token](../token_chunking_comparison.json).
- Baseline v1: [label](../semantic_retrieval_ground_truth.json), [hasil](../semantic_retrieval_benchmark.json), [skrip benchmark lama](../benchmark_semantic_retrieval.py).
- Studi v2: [protokol](../retrieval_study_protocol_v2.json), [label](../retrieval_study_labels_v2.json), [korpus](../reviewed_corpus_v2.json), [verifikasi](../retrieval_study_verification_v2.json).
- Studi v3: [protokol](../quality-v3/protocol.json), [lock awal](../quality-v3/lock.json), [amendment development](../quality-v3/development_amendment.json), [lock r2](../quality-v3/lock-r2.json), [manifest final test](../quality-v3/final_test_manifest.json).
- Bukti v3: [audit korpus](../quality-v3/verification.json), [review visual](../quality-v3/visual_review.json), [verifikasi akhir](../quality-v3/final_verification.json), [catatan hash pascaformat](../quality-v3/postprocessing_notes.json).
- [Anotasi independen kosong](../quality-v3/independent_annotation_template.json) tetap belum menjadi ground truth manusia yang selesai.

Skrip historis yang menghasilkan laporan dapat menolak overwrite atau
menimpa path lama. Jalur verifikasi sekarang adalah [evaluator resmi](../benchmarks/README.md).
Cache model, indeks dan render lokal termasuk GENERATED_LOCAL_ARTIFACT;
tidak diarsipkan sebagai hasil ilmiah pengganti. Tidak ada berkas
UNKNOWN_DEPENDENCY yang dihapus, dan tidak ada duplikat historis yang
dinyatakan REDUNDANT_VERIFIED hanya karena bytes-nya sama.
