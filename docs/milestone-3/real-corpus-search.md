# Integrasi semantic search korpus nyata — indeks eksperimen

Sebanyak **130 chunk dari 15 dokumen** pada
[knowledge_chunks.json](../../data/corpus/processed/knowledge_chunks.json)
diindeks melalui [CLI yang ada](../../src/proyek_certan/knowledge/cli.py) ke
`.local/chroma-corpus-m3`. Path ini berbeda dari `.local/chroma` yang dipakai
untuk data sintetis dan diabaikan Git. Collection `certan_knowledge`
menggunakan cosine distance. Model yang sudah dikonfigurasi adalah
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, dengan
embedding **384 dimensi**. Tidak ada perubahan pada implementasi embedding,
vector store, retrieval, maupun kode Milestone 1/2.

Jalankan ulang dari root repository:

```powershell
uv run --frozen --no-sync python -m proyek_certan.knowledge.cli index --input data/corpus/processed/knowledge_chunks.json --db .local/chroma-corpus-m3
uv run --frozen --no-sync python -m proyek_certan.knowledge.cli search --db .local/chroma-corpus-m3 --query "VLAN 9 pada Open vSwitch tidak terisolasi" --top-k 3
```

Indexing awal berhasil dengan `{"indexed": 130, "collection_count": 130}`
dalam **51,673 detik**. Setelah metadata status DRAFT dan review ditambahkan,
upsert ulang 130 ID berhasil dalam **63,344 detik**; jumlah record tetap 130.
Percobaan awal sebelum itu sempat gagal dengan `WinError 4551` saat memuat
`torch_python.dll` karena kebijakan Application Control Windows. Pemanggilan
ulang berhasil, dan dua integration test model nyata juga lulus. Catatan ini
disimpan agar kegagalan yang bersifat tidak menetap tidak disembunyikan.

Proses Python baru membuka database dan memeriksa bahwa semua 130 ID, teks,
serta metadata sama dengan JSON input, mencakup DOC01–DOC15. DOC-09/10 tetap
memiliki `publication_status: DRAFT menurut halaman sumber` pada metadata
setiap chunk; lima dokumen audit memiliki `review_required: true`. Pencarian
`top_k=3` mengembalikan teks, judul, section, URL sumber, dan cosine similarity.
Hasil lengkap setiap kueri ada di [laporan JSON](../../evaluation/real_corpus_search.json).

| Kueri bahasa Indonesia | Top-1 | Cosine similarity | Catatan |
|---|---|---:|---|
| WiFi kampus tersambung, internet tidak dapat diakses | DOC13-0006 | 0,5893 | DOC08 muncul di posisi 2; DOC01 tidak masuk top-3 |
| Nama domain gagal di-resolve / DNS server dan klien | DOC02-0008 | 0,6758 | Ketiga hasil top-3 dari DOC02 |
| Klien tidak mendapat alamat IP DHCP | DOC03-0000 | 0,7443 | DOC03 juga posisi 2 |
| VLAN 9 Open vSwitch dan OpenFlow | DOC06-0008 | 0,7598 | Ketiga hasil top-3 dari DOC06 |
| Eskalasi insiden P1 dan komunikasi pengguna | DOC09-0006 | 0,5089 | DOC09 juga posisi 2; DOC04 posisi 3 |

Angka similarity adalah `1 - cosine_distance`, bukan tingkat keyakinan
diagnosis. Kueri belum memiliki label relevansi, sehingga tabel ini adalah
smoke test teknis, bukan bukti akurasi retrieval. Kueri WiFi dan eskalasi
memperlihatkan hasil yang perlu dievaluasi lebih lanjut.

## Kesiapan produksi

**Indeks ini belum layak disebut selesai untuk produksi.** Model membatasi
input pada **128 token**, sementara **115 dari 130 chunk** mempunyai panjang
token mentah di atas batas tersebut (maksimum terukur 675). Encoder dapat
memotong bagian akhir chunk saat membuat embedding; teks lengkap tetap
tersimpan di Chroma, tetapi sebagian isi mungkin tidak terwakili oleh vektornya.
Perlu eksperimen ulang dengan chunk yang mengikuti batas token model, kemudian
reindexing ke database terpisah dan evaluasi retrieval berlabel.

Lima dokumen berikut juga memerlukan review isi sebelum indexing final:

| Dokumen | Temuan | Tindakan manual |
|---|---|---|
| DOC-06 | Beberapa perintah `ovs-vsctl` menyatu dengan prosa pada satu baris TXT | Bandingkan format perintah dengan FAQ resmi; jangan menambah langkah |
| DOC-09 | Halaman SOP sumber berstatus DRAFT | Pastikan status/persetujuan sebelum dipakai sebagai SOP resmi |
| DOC-10 | Halaman SOP sumber berstatus DRAFT | Pastikan status/persetujuan sebelum dipakai sebagai SOP resmi |
| DOC-11 | Baris PDF terpotong, nomor halaman/daftar isi terbawa | Periksa urutan prosedur dan tabel terhadap PDF |
| DOC-13 | Baris PDF terpotong mengikuti tata letak halaman | Periksa urutan kebijakan dan prosedur terhadap PDF |

Temuan terukur berasal dari [audit korpus](../../evaluation/corpus_chunking.json).
Tidak ada teks sumber yang diubah untuk menjalankan eksperimen ini.

Verifikasi akhir memakai `CERTAN_RUN_MODEL_TESTS=1` dan
`uv run --frozen --no-sync python -m pytest -q`: **168 passed**.
Satu tes tambahan mengindeks 130 chunk nyata ke database sementara dengan
encoder stub untuk memeriksa cakupan, metadata, dan persistensi lintas proses;
tes model asli memverifikasi embedding dan retrieval dengan model sungguhan.
`uv lock --check` lulus. Pemeriksaan `git diff --check` untuk file tahap ini
lulus; pemeriksaan seluruh working tree menandai trailing whitespace pada
`src/proyek_certan/__init__.py`, perubahan terpisah yang tidak disentuh tahap ini.
