# Panduan utama Milestone 3 CERTAN

Milestone 3 membangun basis pengetahuan jaringan dan semantic retrieval yang
dapat ditelusuri. Pipeline aktif menggunakan satu korpus, satu profil chunking
dan satu rute indexing. Ia mengembalikan rujukan, belum membuat jawaban atau
keputusan operasional otomatis.

## Dataset dan korpus final

[Korpus final](../../data/corpus/final/README.md) memuat 15 TXT DOC01–DOC15
dan 487 chunk dari reviewed-v3 `v3_t96_w10`. Delapan sumber diagnosis jaringan,
empat sumber proses insiden, dan tiga kebijakan jaringan mencakup Microsoft,
Open vSwitch dan beberapa universitas. Sebanyak 13 sumber berbahasa Inggris
dan dua Indonesia. Representativitasnya berlaku untuk ruang lingkup prototipe,
bukan seluruh insiden atau kebijakan kampus lokal.

[Manifest aktif](../../data/corpus/final/manifest.json) menyimpan SHA-256,
path aktif/aslinya, sumber, publisher, bahasa, hak penggunaan, status publikasi,
riwayat transformasi dan konfigurasi. Tepat 15 [PDF asli](../../data/corpus/raw/)
tetap pada lokasi awal. DOC-09/10 masih DRAFT; tidak ada pengesahan SOP lokal.

## Ingestion dan cleaning

Alur riset adalah PDF sumber → ekstraksi resmi yang dapat diperiksa → TXT
reviewed-v2/v3 → chunk token-aware → embedding → indeks persisten. Sebanyak
13 PDF sumber tidak menyediakan ekstraksi teks yang memadai; teksnya berasal
dari halaman HTML resmi, dengan provenance tetap dicatat. DOC-11/13 memakai
teks PDF native. [Persiapan](corpus-preparation.md), [ingestion](corpus-ingestion.md)
dan [audit v3](final-quality-v3.md) menjelaskan perbedaan metode tersebut.

Cleaning menghapus page furniture yang terverifikasi dan menyambung pemenggalan
baris yang aman. V3 mempertahankan urutan token substantif v2. Status DRAFT,
placeholder, peringatan sumber dan masalah layout yang belum aman dipertahankan.
Cleanup repository hanya menyalin bytes v3; tidak menjalankan cleaning/chunking
ulang dan tidak menulis ulang laporan riset beku.

## Konfigurasi chunking final

| Parameter | Nilai resmi |
|---|---|
| Profil | `v3_t96_w10` |
| Batas chunk | 96 token model termasuk dua special tokens |
| Overlap | Diminta 10 **kata**, dibatasi anggaran token dan batas bagian |
| Batas input model | 128 token |
| Jumlah | 487 chunk; 15 document_id unik |
| Panjang aktual | Minimum 19, median 84, maksimum 96 token; nol di atas batas model |

Anggaran 96 memberi ruang terhadap batas 128 dan mengurangi pencampuran bagian
panjang. Tokenizer model yang sama mengukur chunk; satuan overlap tetap kata,
bukan token. Overlap menjaga konteks pada batas potongan sambil menambah biaya
penyimpanan dan kemiripan antar-chunk. Chunking mempertimbangkan bagian dan
menjaga cakupan urutan kata sumber. Pilihan ini meneruskan profil yang sudah
digunakan dan diaudit; bukan klaim optimum universal.

Profil 120/12 dan 96/0 adalah ablation historis. Buktinya tetap ada dalam
[korpus v3](../../evaluation/reviewed_corpus_v3.json) dan [eksperimen historis](../../evaluation/archive/README.md),
tetapi tidak menjadi input pipeline utama. [Eksperimen token awal](token-aware-chunking.md)
mencatat keadaan versi v1; angka 484 di sana tidak menggantikan angka final 487.

## Embedding dan metadata

Model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` dipakai
untuk bahasa kueri Indonesia dan mayoritas teks Inggris. Encoder menghasilkan
384 dimensi float32, normalisasi L2, dimuat secara lazy dan digunakan kembali.
Model kueri dan indeks wajib sama. Pilihan ini sesuai kebutuhan bilingual dan
skala prototipe; belum ada pembandingan lintas keluarga embedding.

Metadata mempertahankan document_id, sumber, judul, bagian, indeks chunk,
publisher, jenis dokumen, URL sumber terverifikasi, versi, hash PDF/TXT,
metode ekstraksi, license/status publikasi jika tersedia dan review note.
`metadata.text_file` tetap path asal reviewed-v3; `documents.active_text_file`
di manifest menunjukkan salinan aktif. Ini sengaja mempertahankan bytes
penelitian, bukan dua versi teks aktif.

Page span ditambahkan hanya saat seluruh kata chunk cocok persis dan unik
dengan teks PDF. Pada DOC-11/13, 126 dari 127 chunk memiliki span exact;
chunk lain tidak diberi halaman perkiraan. Tidak ada page span yang dikarang
untuk 13 sumber hasil HTML.

## Persistent ChromaDB dan rute final

```bash
uv run --locked python -m proyek_certan.knowledge.final_cli verify
uv run --locked python -m proyek_certan.knowledge.final_cli index
uv run --locked python -m proyek_certan.knowledge.final_cli verify --index
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Bagaimana diagnosis resolusi nama DNS pada klien?" --top-k 5
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Bagaimana diagnosis resolusi nama DNS pada klien?" --document-level --top-k 5
```

Jalankan dari root repository. [CLI resmi](../../src/proyek_certan/knowledge/final_cli.py)
membaca [path dan pemeriksaan terpusat](../../src/proyek_certan/knowledge/final_corpus.py).
Database resmi `.local/chroma-corpus-final`, cache `.cache/models`, collection
`certan_knowledge`, `PersistentClient`, HNSW cosine, explicit embeddings dan
telemetry nonaktif. HNSW saat diverifikasi menggunakan ef_construction=100,
ef_search=100 dan max_neighbors=16; implementasi store tidak diubah oleh cleanup.

Indexing memakai upsert dan memeriksa seluruh ID, teks, metadata, dimensi serta
norma vektor. Database kosong dapat diisi; database berisi data campuran atau
stale ditolak sebelum encoding. Pengulangan index hanya diizinkan bila indeks
yang sudah ada cocok persis. `--db` tersedia untuk pengujian/recovery terisolasi;
tidak mengganti profil atau input final. CLI memverifikasi corpus terlebih
dahulu dan menolak search bila indeks belum dibuat. Ia tidak menghapus database.

[CLI generik](../../src/proyek_certan/knowledge/cli.py) dan utilitas builder lama
dipertahankan untuk kompatibilitas/penelitian. Default `.local/chroma` pada
API generik adalah perilaku lama; hanya rute final di atas yang menjadi
instruksi operasional sekarang. [Kontrak API](semantic-search.md) tetap berguna
sebagai referensi teknis historis.

## Semantic retrieval

Ranking memakai `similarity = 1 - cosine_distance`, tanpa bonus label, intent,
guardrail atau title reranking. Default mengembalikan chunk. Opsi
`--document-level` memilih chunk dengan cosine tertinggi untuk setiap dokumen
dari 100 kandidat, dengan urutan seri stabil. Deduplikasi mengurangi pengulangan
hasil; tidak membuktikan peningkatan akurasi. Similarity bukan probabilitas.

Tidak ada threshold abstention yang diadopsi. Angka 0,5 dan 0,6 dalam penelitian
adalah konfigurasi pengukuran historis; CLI final tidak mengaktifkannya sebagai
jaminan penolakan OOD. Hasil perlu pemeriksaan manusia.

## Benchmark dan hasil aktual

[Evaluator resmi](../../evaluation/benchmarks/README.md) memeriksa integritas dan
mereplay aritmetika dari observasi beku. `--live` menguji indeks final serta
15 kueri legacy, tanpa menjalankan ulang retrieval validation/final test.

```bash
uv run --locked python evaluation/benchmarks/final_pipeline.py
uv run --locked python evaluation/benchmarks/final_pipeline.py --live
```

| Split beku | Pengukuran semantic baseline |
|---|---|
| Legacy: 12 relevan + 3 OOD | Recall@3 0,8750; MRR 0,8056; Top-1 relevan 8/12 |
| Evaluation v2: 18 relevan + 12 OOD | Recall@3 0,9444; MRR 0,8750; FAR 3/12 pada threshold 0,5 |
| Final test v3: 24 relevan + 24 OOD | P@1 0,7083; P@3 0,3194; R@3 0,9167; R@5 0,9583; MRR 0,8122; FAR 18/24 dan FRR 0/24 pada threshold 0,5 |

Precision/Recall dirata-ratakan pada kueri positif dan dokumen unik; MRR
dibatasi 100 kandidat chunk. FAR adalah OOD yang diterima dibagi seluruh OOD,
FRR adalah kueri positif yang ditolak dibagi seluruh positif. Split berbeda
tidak dibandingkan sebagai kenaikan langsung. Ground truth dan hasil tidak
diubah oleh cleanup.

Guard final menurunkan FAR ke 2/24 tetapi menaikkan FRR ke 7/24. Title reranking
memberi delta MRR +0,02366 dengan CI 95% [-0,04094; +0,09107]. Keduanya ditolak
berdasarkan aturan sebelumnya; tidak menjadi runtime aktif. [Hasil terpisah](../../evaluation/results/README.md)
dan [kandidat ditolak](../../evaluation/experiments/README.md) mempertahankan
bukti negatifnya. [Laporan cleanup](repository-cleanup.md) membandingkan
struktur, hashes dan regresi aktual sebelum/sesudah.

## Known limitations dan kesiapan

WiFi diagnosis masih menempatkan DOC-13 di atas DOC-01 (rank 6 pada kueri
legacy); deduplikasi tidak menyelesaikan kekeliruan maksud diagnosis/kebijakan.
FAR historis tinggi, tabel/diagram DOC-11 belum seluruhnya terstruktur aman,
dan DOC-09/10 belum disahkan. Label baru masih disusun oleh pihak yang sama;
[anotasi manusia independen](annotation-guide-v3.md) belum selesai.

Korpus tidak merepresentasikan SOP lokal atau kondisi jaringan real time.
Repository siap mendukung laporan prototipe dengan hasil serta batasannya;
seluruh deskriptor nilai 100 dan penggunaan produksi belum terbukti.

## Navigasi sejarah penelitian

- v1: [validasi](corpus-validation.md), [persiapan](corpus-preparation.md), [smoke retrieval](real-corpus-search.md), [benchmark legacy](semantic-retrieval-benchmark.md), [audit awal](final-audit.md).
- v2: [peningkatan terarah](directed-improvement-v2.md), [protokol](../../evaluation/retrieval_study_protocol_v2.json).
- v3: [audit dan eksperimen](final-quality-v3.md), [inventaris tahap v3](change-inventory-v3.md), [protokol/arsip](../../evaluation/archive/README.md).

Laporan lama dibaca menurut versi/tanggalnya. Instruksi final sekarang hanya
yang tercantum pada panduan ini dan manifest aktif.
