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
Kode Milestone 1/2, embedding, vector store, retrieval, dependensi, lockfile, serta
PDF sumber tidak diubah. Tidak dilakukan commit atau push.
