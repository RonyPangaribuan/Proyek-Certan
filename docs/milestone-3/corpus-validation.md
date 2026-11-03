# Validasi korpus PDF sebelum ingestion

Validator berada pada [modul corpus](../../src/proyek_certan/corpus/validation.py).
Modul ini hanya membaca PDF: tidak menjalankan OCR, ingestion, chunking,
embedding, atau akses vector store. Tidak ada dependensi baru.

## Menjalankan ulang

Dari root repository, gunakan environment `uv` yang sudah tersedia:

```powershell
uv run --frozen --no-sync python -m proyek_certan.corpus.validation
```

Secara default, validator mencari PDF secara rekursif di
`data/corpus/raw/` (termasuk ekstensi `.PDF`), memeriksa jumlahnya terhadap
15 dokumen, dan menyimpan:

- [Ringkasan CSV](../../evaluation/pdf_validation.csv): satu baris per dokumen.
- [Laporan JSON](../../evaluation/pdf_validation.json): metadata metode, ringkasan,
  SHA-256 dokumen sumber, statistik dan preview teks per halaman, serta pesan error.

Lokasi dan ambang dapat diatur:

```powershell
uv run --frozen --no-sync python -m proyek_certan.corpus.validation --input-dir data/corpus/raw --output-dir evaluation --expected-count 15 --min-page-chars 80
```

Laporan dengan nama yang sama diganti saat dijalankan ulang. PDF sumber tidak
ditulis ulang. Nomor halaman pada laporan berbasis 1, mengikuti urutan fisik PDF,
bukan nomor halaman yang tercetak pada dokumen.

## Definisi metrik dan status

- `character_count`: jumlah `len(text)` dari hasil mentah
  `pypdf.PageObject.extract_text()`, termasuk whitespace. Teks tidak dinormalisasi
  sebelum dihitung. Karakter dari halaman gagal tidak masuk hitungan.
- `empty_page_count`: halaman yang ekstraksinya berhasil tetapi `text.strip()`
  kosong, termasuk hasil `None`. Halaman gagal dicatat terpisah dalam
  `failed_page_numbers`, bukan dianggap kosong.
- Jumlah halaman/halaman kosong bernilai `null` jika dokumen tidak dapat dibuka
  atau memerlukan password; angka 0 tidak dipakai untuk menyamarkan ketidakpastian.
- `success`: setidaknya satu halaman menghasilkan teks dan tidak ada error.
  Sebagian halaman masih dapat kosong atau memiliki flag kualitas.
- `partial`: sebagian teks berhasil diambil tetapi ada error halaman/dokumen.
- `no_text`: seluruh halaman berhasil diperiksa tetapi tidak menghasilkan teks.
- `failed`: PDF gagal dibaca, seluruh ekstraksi halaman gagal, atau tidak punya halaman.
- `encrypted`: membutuhkan password. Hanya password kosong yang dicoba untuk
  dokumen yang mengizinkan pembacaan tanpa password pengguna.

`readiness` memisahkan hasil ekstraksi dari keputusan kelayakan:

| Nilai | Makna |
|---|---|
| `ready` | Ekstraksi sukses tanpa flag heuristik/peringatan parser |
| `review` | Ekstraksi sukses; ada halaman/karakter/peringatan yang perlu ditinjau |
| `blocked` | Ekstraksi gagal, parsial, terenkripsi, atau tanpa teks |

## Flag kualitas

| Flag | Pemicu |
|---|---|
| `empty_text` | Tidak ada teks non-whitespace |
| `sparse_text` | Halaman tidak kosong tetapi berisi kurang dari 80 karakter non-whitespace secara default |
| `replacement_characters` | Ditemukan U+FFFD, indikasi potensi kegagalan pemetaan karakter |
| `unexpected_control_characters` | Karakter kontrol selain newline, carriage return, tab, dan form feed |
| `private_use_characters` | Karakter Unicode private-use, misalnya dari font simbol |
| `unmapped_glyphs` | Penanda `(cid:angka)` muncul dalam teks |
| `low_alphanumeric_ratio` | Pada halaman cukup panjang, rasio huruf/angka terhadap karakter non-whitespace kurang dari 50% |

`quality_issues` memetakan setiap flag ke nomor halamannya. Peringatan logger
`pypdf` dan Python disimpan dalam `parser_warnings`. Error halaman tetap dicatat,
dan pemeriksaan melanjutkan halaman/dokumen berikutnya.

Flag bersifat heuristik. Halaman kosong dapat berupa pemisah; teks sedikit dapat
berupa sampul atau diagram; private-use dapat berupa bullet. Flag tersebut tidak
otomatis membuktikan dokumen rusak atau perlu OCR. Sebaliknya, `ready` juga tidak
membuktikan akurasi makna, urutan baca, isi tabel, dan kelengkapan teks pada gambar.
Preview per halaman membantu peninjauan awal, tetapi bukan pengganti pemeriksaan
isi dan tata letak PDF sebelum menentukan perlakuan saat ingestion.

## Exit code dan pengujian

- `0`: jumlah dokumen sesuai dan tidak ada `blocked`; `review` tetap harus ditinjau.
- `1`: setidaknya satu dokumen `blocked`.
- `2`: direktori/penulisan laporan bermasalah, argumen tidak valid, atau jumlah
  PDF tidak sesuai. Untuk ketidaksesuaian jumlah, laporan tetap disimpan.

Pengujian khusus menggunakan PDF sintetis yang dibuat dengan `pypdf`, tanpa
mengubah korpus asli:

```powershell
uv run --frozen --no-sync python -m pytest tests/corpus/test_pdf_validation.py -q
uv run --frozen --no-sync python -m pytest -q
```

Pengujian mencakup PDF normal, kosong, nol halaman, rusak, terenkripsi, kegagalan
per halaman, peringatan parser, heuristik kualitas, pencarian rekursif, ekspor
laporan, ketidaksesuaian jumlah dokumen, serta exit code.
