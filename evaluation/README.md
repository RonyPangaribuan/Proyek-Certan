# Hasil validasi korpus Milestone 3

Validasi aktual dilakukan pada branch `feature/milestone-3-vector-db`, menggunakan
environment `.venv` yang sudah tersedia melalui `uv 0.12.10`, Python 3.11.9,
dan `pypdf 6.21.4`. Waktu UTC persis dan SHA-256 setiap dokumen tersimpan pada
[laporan JSON](./pdf_validation.json).

**Korpus belum layak dilanjutkan seluruhnya ke ingestion dan chunking.**
Dari 15 PDF (95 halaman), hanya 2 dokumen (21 halaman) menghasilkan teks.
Tiga belas dokumen lainnya (74 halaman) menghasilkan teks kosong pada seluruh
halamannya. Jumlah karakter total yang berhasil diekstraksi adalah 40.890.

| Dokumen | Halaman | Karakter | Halaman teks kosong | Status ekstraksi | Potensi masalah |
|---|---:|---:|---:|---|---|
| [DOC01_WiFi.pdf](../data/corpus/raw/DOC01_WiFi.pdf) | 2 | 0 | 2 | `no_text` | Seluruh halaman tanpa teks |
| [DOC02_DNS.pdf](../data/corpus/raw/DOC02_DNS.pdf) | 6 | 0 | 6 | `no_text` | Seluruh halaman tanpa teks |
| [DOC03_DHCP_Server.pdf](../data/corpus/raw/DOC03_DHCP_Server.pdf) | 5 | 0 | 5 | `no_text` | Seluruh halaman tanpa teks |
| [DOC04_DHCP_Client.pdf](../data/corpus/raw/DOC04_DHCP_Client.pdf) | 1 | 0 | 1 | `no_text` | Seluruh halaman tanpa teks |
| [DOC05_TCP_IP.pdf](../data/corpus/raw/DOC05_TCP_IP.pdf) | 6 | 0 | 6 | `no_text` | Seluruh halaman tanpa teks |
| [DOC06_LAN_Switch.pdf](../data/corpus/raw/DOC06_LAN_Switch.pdf) | 30 | 0 | 30 | `no_text` | Seluruh halaman tanpa teks |
| [DOC07_Packet_Loss.pdf](../data/corpus/raw/DOC07_Packet_Loss.pdf) | 3 | 0 | 3 | `no_text` | Seluruh halaman tanpa teks |
| [DOC08_Authentication.pdf](../data/corpus/raw/DOC08_Authentication.pdf) | 6 | 0 | 6 | `no_text` | Seluruh halaman tanpa teks |
| [DOC09_Service_Desk.pdf](../data/corpus/raw/DOC09_Service_Desk.pdf) | 4 | 0 | 4 | `no_text` | Seluruh halaman tanpa teks |
| [DOC10_Incident_Handling.pdf](../data/corpus/raw/DOC10_Incident_Handling.pdf) | 4 | 0 | 4 | `no_text` | Seluruh halaman tanpa teks |
| [DOC11_Incident_Management_UCF.pdf](../data/corpus/raw/DOC11_Incident_Management_UCF.pdf) | 16 | 31.655 | 0 | `success` | Tidak ada flag heuristik |
| [DOC12_Security_Incident.pdf](../data/corpus/raw/DOC12_Security_Incident.pdf) | 3 | 0 | 3 | `no_text` | Seluruh halaman tanpa teks |
| [DOC13_Network_Administration.pdf](../data/corpus/raw/DOC13_Network_Administration.pdf) | 5 | 9.235 | 0 | `success` | Tidak ada flag heuristik |
| [DOC14_Acceptable_Use.pdf](../data/corpus/raw/DOC14_Acceptable_Use.pdf) | 3 | 0 | 3 | `no_text` | Seluruh halaman tanpa teks |
| [DOC15_Network_Management.pdf](../data/corpus/raw/DOC15_Network_Management.pdf) | 1 | 0 | 1 | `no_text` | Seluruh halaman tanpa teks |
| **Total** | **95** | **40.890** | **74** | **2 sukses, 13 tanpa teks** | |

Seluruh dokumen dapat dibuka dan jumlah halamannya terbaca. Tidak ada exception
ekstraksi per halaman, kegagalan pembukaan, kebutuhan password, maupun peringatan
parser pada pengujian aktual. Jadi `no_text` berarti ekstraksi mengembalikan teks
kosong, bukan validator mengalami crash. Nomor halaman kosong tercatat lengkap
pada JSON dan [CSV](./pdf_validation.csv).

Pemeriksaan tambahan terhadap resources halaman pertama setiap PDF menunjukkan
tidak ada resource font pada halaman pertama semua 13 dokumen `no_text`;
beberapa memiliki XObject gambar. Kedua dokumen yang menghasilkan teks memiliki
resource font pada halaman pertamanya. Temuan ini konsisten dengan konten yang
disimpan sebagai gambar atau outline grafis, tetapi belum merupakan pemeriksaan
visual menyeluruh atau bukti bahwa semua dokumen merupakan hasil scan.

## Keputusan sebelum ingestion

- Dua dokumen berstatus `success` lolos pemeriksaan ekstraksi otomatis. Ketepatan
  urutan baca, tabel, dan kesesuaian isi masih perlu ditinjau sebelum chunking.
- Tiga belas dokumen `no_text` berstatus `blocked`. Jangan memasukkannya ke
  ingestion berbasis teks karena akan menghasilkan konten kosong. Periksa PDF
  sumber atau cari versi asli yang memiliki teks yang dapat diseleksi/diekstraksi.
- Tidak ada OCR yang dijalankan. Jika versi sumber dengan teks tidak tersedia,
  keputusan penanganan dokumen tersebut menjadi tahap terpisah setelah review.

## Pengujian yang benar-benar dijalankan

```powershell
uv run --frozen --no-sync python -m pytest tests/corpus/test_pdf_validation.py -q
# 18 passed in 0.97s

uv run --frozen --no-sync python -m pytest -q
# 148 passed, 2 skipped in 22.58s

uv run --frozen --no-sync python -m proyek_certan.corpus.validation
# 15 dokumen, 95 halaman; 2 success, 13 no_text; exit code 1
```

Exit code 1 pada validasi korpus memang menandai adanya dokumen `blocked`.
Dua tes yang dilewati adalah integrasi model embedding nyata yang secara default
memerlukan `CERTAN_RUN_MODEL_TESTS=1`; tidak diaktifkan untuk tugas validasi PDF.

Panduan metrik, konfigurasi, flag kualitas, dan exit code tersedia pada
[dokumentasi validator](../docs/milestone-3/corpus-validation.md).
Pada tahap validasi PDF awal, kode Milestone 1/2, embedding, vector store,
retrieval, dependensi, lockfile, serta PDF sumber tidak diubah.

## Tindak lanjut: persiapan teks korpus

Laporan terkini tersedia pada [corpus_processing.json](./corpus_processing.json),
dengan metadata dan URL resmi pada
[corpus_manifest.json](../data/corpus/corpus_manifest.json). Berkas hasil berada
di [data/corpus/processed/](../data/corpus/processed/). Tahap ini menghasilkan
**14 dari 15 dokumen**, total **122.302 karakter**: 12 dari HTML resmi, 2 dari
`pypdf`. DOC-06 memerlukan tindakan manual. Tidak ada OCR atau perubahan PDF asli.

| ID | Panjang teks | Metode | Status | Catatan |
|---|---:|---|---|---|
| DOC01 | 4.367 | HTML Microsoft Learn | processed | |
| DOC02 | 13.940 | HTML Microsoft Learn | processed | |
| DOC03 | 9.372 | HTML Microsoft Learn | processed | |
| DOC04 | 1.814 | HTML Microsoft Learn | processed | |
| DOC05 | 15.004 | HTML Microsoft Learn | processed | |
| DOC06 | 0 | — | manual_required | Ketentuan reproduksi Cisco perlu dipastikan |
| DOC07 | 8.103 | HTML Microsoft Learn | processed | |
| DOC08 | 5.766 | HTML Microsoft Learn | processed | |
| DOC09 | 7.611 | HTML DTSI UHB | processed | Sumber berstatus DRAFT |
| DOC10 | 4.600 | HTML DTSI UHB | processed | Sumber berstatus DRAFT |
| DOC11 | 30.280 | pypdf PDF asli | processed | |
| DOC12 | 4.178 | HTML University of Utah | processed | |
| DOC13 | 8.996 | pypdf PDF asli | processed | |
| DOC14 | 5.712 | HTML Western Michigan University | processed | |
| DOC15 | 2.559 | HTML Indiana University Bloomington | processed | |

Skrip menggunakan satu request per halaman HTML yang ditetapkan dalam manifest,
memeriksa `robots.txt`, dan menolak URL redirect, halaman terlalu pendek, atau
respons yang bukan HTML. Pembersihan membuang navigasi, footer, cookie,
komentar template, dan widget lain; heading, langkah, kode, serta tabel dasar
dipertahankan. Setiap file diuji sebagai UTF-8 dan dicocokkan panjang teks serta
SHA-256-nya dengan laporan. Teks halaman HTML dapat berbeda dari tampilan PDF
yang dicetak sebelumnya jika sumber berubah; peninjauan isi sebelum chunking
tetap diperlukan.

Sumber Microsoft Learn didokumentasikan dengan atribusi dan
[lisensi CC BY 4.0](https://github.com/MicrosoftDocs/SupportArticles-docs/blob/main/LICENSE)
pada manifest. DOC-06 ditunda karena
[ketentuan reproduksi Cisco](https://www.cisco.com/c/en/us/about/brand-center/copyright-use.html)
tidak memberikan izin yang jelas untuk menaruh salinan teks penuh dalam korpus
repository ini. Tindakan manual: pastikan izin atau sediakan teks alternatif
resmi yang boleh disimpan dan diproses. Jangan mengisi file DOC-06 dengan teks
hasil tebakan.

Panduan menjalankan ulang dan batasan ekstraksi ada pada
[dokumentasi persiapan korpus](../docs/milestone-3/corpus-preparation.md).
Dependensi langsung `requests` dan `beautifulsoup4` ditambahkan melalui `uv`.
Pengujian akhir: `155 passed, 2 skipped`; `uv lock --check` lulus. Hash seluruh
15 PDF asli tetap sama dengan laporan validasi awal.
Tidak ada commit atau push.
