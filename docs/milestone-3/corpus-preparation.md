# Persiapan teks korpus Milestone 3

Korpus sumber dan metadata resmi didaftarkan dalam
[corpus_manifest.json](../../data/corpus/corpus_manifest.json).
[prepare.py](../../src/proyek_certan/corpus/prepare.py) menulis teks UTF-8 ke
[processed/](../../data/corpus/processed/) dan status per dokumen ke
[corpus_processing.json](../../evaluation/corpus_processing.json).
PDF pada [raw/](../../data/corpus/raw/) dibaca untuk validasi hash atau
ekstraksi DOC-11/DOC-13, tetapi tidak ditulis ulang. DOC-06 menggunakan
[FAQ VLAN Open vSwitch](https://docs.openvswitch.org/en/stable/faq/vlan/)
karena PDF cetaknya tidak menghasilkan teks pada `pypdf`. Pipeline embedding,
vector store, retrieval, ingestion, dan chunking tidak dipanggil.

Jalankan dari root repository dengan environment yang sudah ada:

```powershell
uv run --frozen --no-sync python -m proyek_certan.corpus.prepare
```

Exit code `0` berarti semua dokumen berhasil disiapkan. Exit code `1` berarti
masih ada dokumen `manual_required`; laporan tetap dibuat. File hasil lama
digunakan ulang bila hash PDF dan teks, URL sumber, serta panjang teks cocok
dengan laporan sebelumnya. File yang tidak cocok akan diproses ulang.

## Provenance dan akses

- Sumber HTML dipilih dari judul metadata PDF dan dicocokkan ke URL resmi
  penerbit. Satu halaman HTML tertentu diambil per dokumen dengan `requests`,
  tanpa pencarian otomatis, crawling tautan, bypass, ataupun OCR.
- Skrip memeriksa `robots.txt` per host sebelum halaman diakses. Jika URL
  dilarang, akses gagal, redirect terjadi, respons bukan HTML, isi utama tidak
  ditemukan, atau hasil terlalu pendek, status menjadi `manual_required`.
  `robots.txt` yang tidak tersedia dengan HTTP 404 dicatat sebagai catatan,
  bukan dianggap larangan; pengecekan hak penggunaan tetap terpisah.
- DOC-01–05 dan DOC-07–08 berasal dari Microsoft Learn. Teks dokumentasi
  pada [repositori SupportArticles-docs](https://github.com/MicrosoftDocs/SupportArticles-docs)
  diterbitkan dengan [CC BY 4.0](https://github.com/MicrosoftDocs/SupportArticles-docs/blob/main/LICENSE).
  Manifest menyimpan penerbit, URL asli, lisensi, dan informasi bahwa teks
  adalah hasil adaptasi badan HTML ke plain text. Saat mendistribusikan
  korpus, sertakan manifest tersebut untuk atribusi.
- DOC-09/10 dari DTSI Universitas Harapan Bangsa adalah **DRAFT** pada halaman
  resmi. Keduanya dapat dipakai sebagai bahan uji dengan label status itu,
  tetapi jangan diperlakukan sebagai SOP institusi yang sudah disahkan.
- DOC-06 kini berasal dari Open vSwitch Project, kategori troubleshooting VLAN.
  Sumber [FAQ VLAN resmi](https://docs.openvswitch.org/en/stable/faq/vlan/)
  dapat diakses dan `robots.txt` mengizinkan pengambilan halaman tersebut.
  [File sumber FAQ](https://github.com/openvswitch/ovs/blob/main/Documentation/faq/vlan.rst)
  memuat lisensi Apache-2.0. Manifest mencatat lisensi, sumber HTML, serta
  transformasi ke UTF-8 plain text untuk atribusi.

## Pembersihan dan batasnya

`BeautifulSoup` memilih badan artikel, menghapus navigasi, sidebar, cookie,
footer, widget feedback, dan komentar template. Hasil mempertahankan urutan
heading, paragraf, daftar bernomor/bersarang, blok kode, dan isi sel tabel
sebagai teks biasa. `pypdf` membaca setiap halaman DOC-11 dan DOC-13; halaman
kosong akan menahan dokumen tersebut untuk review manual. Teks sumber tidak
diterjemahkan atau ditambah dengan instruksi buatan.

Laporan menyimpan metode, URL sumber, panjang teks, jumlah kata, heading,
item daftar, SHA-256 setiap file teks, dan SHA-256 PDF yang menjadi acuan
hasilnya. Semua PDF sumber dibandingkan dengan SHA-256 pada
[laporan validasi terbaru](../../evaluation/pdf_validation.json). PDF DOC-06
yang baru memiliki hash berbeda dari PDF Cisco lama sehingga hasil sebelumnya
tidak pernah digunakan ulang. PDF lain dan 14 teks lama diverifikasi sebelum
digunakan ulang.

Pembersihan otomatis tidak menjamin urutan baca tabel kompleks, isi diagram,
atau kesamaan sempurna antara HTML saat ini dan PDF yang semula dicetak.
Periksa konten hasil, terutama kebijakan dan SOP, sebelum meneruskan ke chunking.

## Pengujian

```powershell
uv run --frozen --no-sync python -m pytest tests/corpus -q
uv run --frozen --no-sync python -m pytest -q
```

Tes korpus memeriksa pemisahan badan artikel dari navigasi, struktur langkah
dan tabel, pemblokiran halaman pendek/challenge, pembatasan host HTTPS, serta
penghormatan terhadap `robots.txt`. Status dan tindakan manual aktual tersedia
pada [laporan persiapan](../../evaluation/README.md).
