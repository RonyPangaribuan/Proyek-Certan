# Finalisasi kode Milestone 3 (T03)

> Laporan ini merekam audit historis v1. Tindak lanjut lima dokumen berflag,
> temuan URL DOC-13, benchmark 75 kueri, dan hasil eksperimen yang tidak diadopsi
> tersedia dalam [laporan peningkatan v2](./directed-improvement-v2.md).

Audit dilakukan pada branch `feature/milestone-3-vector-db` dengan korpus dan
indeks yang sudah ada. Prototipe ini hanya mencakup ingestion, chunking,
embedding, ChromaDB persisten, retrieval, dan evaluasi. Tidak ada perubahan
terhadap implementasi Milestone 1 atau 2.

## Hasil pemeriksaan

| Komponen | Status | Bukti dan batas |
|---|---|---|
| Struktur, import, dependensi | PASS | Modul korpus dan knowledge terpisah; `uv lock --check` dan suite penuh lulus. Skrip eksperimen tetap tersedia. |
| Manifest, 15 PDF/TXT | PASS | [Audit integritas](../../evaluation/audit_milestone3.py) cocokkan hash 15 PDF dengan laporan validasi, hash dan panjang TXT dengan laporan processing, serta metadata manifest. DOC-11/13 tepat sama dengan ekstraksi ulang PDF lokal. |
| Kualitas isi lima dokumen berflag | WARNING | DOC-06 memiliki dua perintah `ovs-vsctl` pada satu baris; DOC-09/10 DRAFT; DOC-11 memiliki daftar isi/nomor halaman dan hard wrap PDF; DOC-13 memiliki hard wrap PDF. Lihat tinjauan di bawah. |
| Chunking, overlap, cakupan, metadata | PASS | Regenerasi deterministik baseline dan kedua profil cocok persis dengan file JSON; pemeriksaan cakupan kata sumber lulus. Seluruh ID unik, 15 dokumen dan metadata wajib lengkap. |
| Batas token embedding | PASS | Tokenizer asli menghitung special tokens: maksimum 120 untuk 374 chunk dan 96 untuk 484 chunk, di bawah batas model 128. Baseline 130 chunk tetap artefak historis dan tidak memenuhi batas token. |
| Chroma persisten dan isolasi indeks | PASS | Proses audit baru membuka kembali baseline 130, `t120_w12` 374, `t96_w10` 484, dan indeks final 484. Seluruh ID, teks, dan metadata tersimpan cocok dengan file chunk masing-masing. Path final `.local/chroma-corpus-m3-final` terpisah dari tiga path lain. |
| Pencarian dan cosine similarity | PASS | CLI pada proses baru mengembalikan DOC-02 untuk kueri DNS dengan sumber, metadata, dan skor. [Kode retrieval](../../src/proyek_certan/knowledge/retrieval.py) menghitung `similarity = 1 - cosine_distance`; tes mencakup skor batas dan validasi threshold. |
| Benchmark 15 kueri | PASS | [Ground truth](../../evaluation/semantic_retrieval_ground_truth.json) berbasis isi korpus, 12 kueri positif dan 3 OOD berlabel kosong. [Hasil](../../evaluation/semantic_retrieval_benchmark.json) dihitung ulang dengan model asli; Recall@3 0,875 dan MRR 0,8056 untuk `t96_w10`, sama dengan [laporan benchmark](./semantic-retrieval-benchmark.md). |
| Kelayakan jawaban operasional | WARNING | Kueri diagnosis WiFi tetap memilih DOC-13 sebelum DOC-01; hanya tiga kueri OOD; dokumen DRAFT dan review flags belum disetujui sebagai dasar SOP lokal. |

## Tinjauan dokumen berflag

- **DOC-06:** [TXT](../../data/corpus/processed/DOC06_LAN_Switch.txt)
  mempertahankan 10 pasangan Q/A dan contoh perintah VLAN. Satu baris contoh
  `native-tagged` menggabungkan dua perintah; [FAQ sumber Open vSwitch](https://docs.openvswitch.org/en/stable/faq/vlan/)
  menunjukkan konteks perintahnya, tetapi tampilan teks sumber juga merapatkan
  dua perintah. Teks dan indeks tidak diubah dalam audit ini agar bukti benchmark
  tetap merujuk versi korpus yang sama. Perbaikan formatter perlu diuji pada
  HTML asli lalu diikuti regenerasi TXT, laporan hash, semua chunk, empat
  indeks, dan benchmark sebagai versi korpus baru.
- **DOC-09 dan DOC-10:** [TXT service desk](../../data/corpus/processed/DOC09_Service_Desk.txt)
  dan [TXT insiden](../../data/corpus/processed/DOC10_Incident_Handling.txt)
  mempertahankan heading, daftar prosedur, placeholder, serta status DRAFT.
  Halaman sumber [OPS-01](https://docs.dtsi.uhb.ac.id/sop/layanan-ti/dtsi-sop-ops-01/)
  dan [INC-02](https://docs.dtsi.uhb.ac.id/sop/layanan-ti/dtsi-sop-inc-02/)
  juga masih bertanda DRAFT. Keduanya milik Universitas Harapan Bangsa,
  bukan SOP resmi IT Del; angka SLA dan placeholder tidak boleh dipakai sebagai
  instruksi operasional CERTAN.
- **DOC-11:** [TXT](../../data/corpus/processed/DOC11_Incident_Management_UCF.txt)
  cocok persis dengan ekstraksi ulang [PDF lokal](../../data/corpus/raw/DOC11_Incident_Management_UCF.pdf).
  Heading utama dan paragraf prosedur terbaca, tetapi nomor halaman, daftar isi,
  serta hard wrap masih dapat mengganggu pencarian. Rekonstruksi tabel dan
  urutan baca visual belum disahkan secara manual.
- **DOC-13:** [TXT](../../data/corpus/processed/DOC13_Network_Administration.txt)
  cocok persis dengan ekstraksi ulang [PDF lokal](../../data/corpus/raw/DOC13_Network_Administration.pdf).
  Bagian 5.3 tentang Wi-Fi terbaca; hard wrap masih ada. Ketepatan semua tata
  letak visual dan konteks kebijakan belum disahkan secara manual.

Pemeriksaan hash dan ekstraksi lokal tidak membuktikan semua informasi visual
13 PDF yang tidak memiliki text layer telah terwakili oleh halaman HTML. Hasil
review otomatis dan pemeriksaan halaman di atas **bukan persetujuan manual
menyeluruh** terhadap seluruh sumber.

## Masalah yang diperbaiki dan yang tersisa

Hash input baseline pada [laporan pencarian lama](../../evaluation/real_corpus_search.json)
tidak cocok dengan file chunk saat ini. Audit menunjukkan 130 ID, teks, dan
metadata di Chroma sama persis dengan file chunk; hash laporan diperbarui tanpa
mengubah korpus atau indeks. [README utama](../../README.md) sebelumnya masih
menyatakan integrasi korpus nyata belum dilakukan; alur, path indeks final,
perintah, dan batas prototipe kini diperbarui. [Skrip audit](../../evaluation/audit_milestone3.py)
dan [tes konsistensi benchmark](../../tests/knowledge/test_semantic_benchmark_metrics.py)
ditambahkan untuk reproduksi.

Masalah retrieval WiFi dan potensi false positive tidak diperbaiki dengan
menaikkan threshold: DOC-13 yang salah untuk intent diagnosis berskor 0,7374
pada profil terpilih. Tiga OOD ditolak oleh threshold 0,5 dalam benchmark,
tetapi empat kueri positif tetap mempunyai Top-1 yang tidak relevan. Threshold
itu belum cukup untuk penerimaan produksi. Run ulang benchmark mempertahankan
semua metrik agregat; ada sedikit perbedaan ranking pada posisi jauh akibat
pencarian aproksimasi Chroma, sehingga identitas seluruh 100 posisi mentah
tidak dijamin identik antar-run.

## Perintah dan hasil aktual

Dari root repository dengan environment `uv` yang tersedia:

| Perintah | Hasil |
|---|---|
| `uv run --frozen --no-sync python evaluation/audit_milestone3.py` | Lulus; 15 sumber, seluruh chunk, dan empat indeks cocok; maksimum 120/96 token termasuk special tokens. |
| `uv run --frozen --no-sync python evaluation/benchmark_semantic_retrieval.py` | Lulus; `t96_w10` Recall@3 0,875 dan MRR 0,805555..., `t120_w12` 0,791666... dan 0,784722... . |
| `uv run --frozen --no-sync python -m proyek_certan.knowledge.cli index --input data/corpus/processed/knowledge_chunks_t96_w10.json --db .local/chroma-corpus-m3-final` | Berhasil; 484 diindeks, jumlah koleksi 484. |
| CLI `search` pada path final dengan kueri DNS, `--top-k 5` | Berhasil; DOC-02 Top-1, sumber dan similarity ada. |
| `CERTAN_RUN_MODEL_TESTS=1` lalu `uv run --frozen --no-sync python -m pytest -q` | **175 passed** termasuk tes model asli. |
| `uv lock --check` | Lulus; 133 paket resolved. |
| `uv sync --locked --offline` | Lulus; 133 paket resolved, 108 paket diperiksa dari cache lokal. |
| `git diff --check` | Lulus. |

Untuk checkout baru, jalankan ingestion, indexing baseline, eksperimen token,
audit, dan benchmark sesuai [README](../../README.md). Jangan menjalankan skrip
eksperimen pada path database eksperimen yang sudah ada; skrip akan menolak
penimpaan agar hasil tidak tercampur.

**Keputusan:** kode Milestone 3 siap difinalisasi sebagai prototipe akademik
T03 pada profil `t96_w10`, dengan WARNING kualitas sumber dan retrieval di atas.
Belum layak disebut production-ready atau dipakai sebagai SOP IT Del.
