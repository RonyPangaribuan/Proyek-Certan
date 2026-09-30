# Rancangan Pengujian CSP

## 1. Tujuan Pengujian

Pengujian pada Milestone 2 dilakukan untuk memastikan bahwa proses penugasan teknisi dan slot waktu menggunakan CSP dapat berjalan sesuai dengan constraint yang telah ditentukan.

Pengujian juga digunakan untuk melihat bagaimana AC-3 dan Backtracking dengan MRV dan LCV bekerja pada beberapa kondisi assignment.

Data pengujian menggunakan data insiden dan data teknisi sintetis yang telah digunakan pada Milestone 2.

Tujuan pengujian adalah:

1. Memastikan assignment yang valid dapat ditemukan.
2. Memastikan assignment yang melanggar constraint dapat ditolak.
3. Memastikan AC-3 dapat melakukan pruning terhadap domain.
4. Memastikan kondisi domain kosong dapat terdeteksi.
5. Memastikan kondisi CSP yang tidak memiliki solusi dapat dikenali.
6. Mengamati perubahan performa ketika ukuran masalah bertambah.

## 2. Data Pengujian

Data utama yang digunakan terdiri dari:

- 12 data insiden pada `sample_incidents.json`.
- 5 data teknisi pada `sample_technicians.json`.
- 3 slot waktu, yaitu `SLOT_1`, `SLOT_2`, dan `SLOT_3`.

Setiap insiden mempunyai kategori yang digunakan untuk menentukan skill teknisi yang sesuai.

Assignment setiap insiden mempunyai bentuk `(teknisi, slot)`.

Contoh:

    INC001 → (TECH004, SLOT_1)

## 3. Skenario Pengujian

### 3.1 Skenario 1 – Kondisi Normal

**Tujuan:**

Memastikan CSP dapat menemukan assignment yang memenuhi seluruh constraint pada kondisi normal.

**Kondisi:**

Data insiden dan teknisi menggunakan data yang tersedia pada dataset.

**Constraint yang diperiksa:**

- Skill teknisi sesuai dengan kategori insiden.
- Teknisi tersedia pada slot yang dipilih.
- Tidak terdapat konflik teknisi dan slot.

**Hasil yang diharapkan:**

Sistem dapat menghasilkan assignment teknisi dan slot yang konsisten dengan seluruh constraint.

### 3.2 Skenario 2 – Skill Tidak Sesuai

**Tujuan:**

Memastikan teknisi yang tidak mempunyai skill yang sesuai tidak dapat diberikan kepada suatu insiden.

**Contoh:**

    INC001 → (TECH001, SLOT_1)

INC001 mempunyai kategori `wifi_slow`, sedangkan TECH001 tidak mempunyai skill `wifi_slow`.

**Hasil yang diharapkan:**

Assignment tersebut dinyatakan tidak valid dan tidak boleh digunakan sebagai solusi CSP.

### 3.3 Skenario 3 – Teknisi Tidak Tersedia

**Tujuan:**

Memastikan teknisi tidak dapat diberikan pada slot yang tidak tersedia.

**Contoh:**

    TECH001
    available_slots = [SLOT_1, SLOT_2]

Assignment:

    INC001 → (TECH001, SLOT_3)

**Hasil yang diharapkan:**

Assignment dinyatakan tidak valid karena TECH001 tidak tersedia pada SLOT_3.

### 3.4 Skenario 4 – Konflik Teknisi dan Slot

**Tujuan:**

Memastikan satu teknisi tidak mendapatkan dua insiden pada slot yang sama.

**Contoh:**

    INC004 → (TECH004, SLOT_1)
    INC010 → (TECH004, SLOT_1)

**Hasil yang diharapkan:**

Assignment dinyatakan tidak valid karena TECH004 mendapatkan dua insiden pada SLOT_1.

### 3.5 Skenario 5 – Domain Berkurang Setelah AC-3

**Tujuan:**

Memastikan AC-3 dapat mengurangi nilai domain yang tidak lagi memungkinkan berdasarkan constraint binary.

**Kondisi:**

Beberapa variable mempunyai pasangan teknisi dan slot yang sama pada domainnya.

Contoh:

    INC001:
    (TECH004, SLOT_1)
    (TECH004, SLOT_2)
    (TECH004, SLOT_3)

    INC010:
    (TECH004, SLOT_1)
    (TECH004, SLOT_2)
    (TECH004, SLOT_3)

AC-3 melakukan pemeriksaan terhadap hubungan kedua variable tersebut.

**Hasil yang diharapkan:**

AC-3 melakukan constraint propagation dan menghapus nilai domain yang tidak mempunyai pasangan yang compatible apabila kondisi tersebut terjadi.

Jumlah nilai domain sebelum dan sesudah proses AC-3 dicatat untuk melihat jumlah pruning.

### 3.6 Skenario 6 – Domain Menjadi Kosong

**Tujuan:**

Memastikan sistem dapat mendeteksi ketika suatu variable tidak mempunyai nilai yang dapat digunakan.

**Kondisi:**

Domain suatu variable menjadi kosong setelah proses pruning.

Contoh:

    D(INC) = {}

**Hasil yang diharapkan:**

Sistem mendeteksi bahwa variable tersebut tidak mempunyai assignment yang memungkinkan dan proses pencarian dapat dihentikan atau dinyatakan gagal untuk kondisi tersebut.

### 3.7 Skenario 7 – CSP Tidak Memiliki Solusi

**Tujuan:**

Memastikan sistem dapat mengenali kondisi ketika seluruh constraint tidak dapat dipenuhi secara bersamaan.

**Kondisi:**

Jumlah insiden atau kondisi assignment dibuat sehingga tidak tersedia kombinasi teknisi dan slot yang dapat memenuhi seluruh constraint.

**Hasil yang diharapkan:**

Sistem tidak menghasilkan assignment yang melanggar constraint dan memberikan status bahwa CSP tidak memiliki solusi.

## 4. Pengujian AC-3

Pengujian AC-3 dilakukan untuk melihat apakah proses constraint propagation dapat mengurangi domain sebelum proses Backtracking.

Hal yang diamati:

1. Ukuran domain sebelum AC-3.
2. Nilai domain yang dihapus.
3. Ukuran domain setelah AC-3.
4. Jumlah proses revisi.
5. Apakah terdapat domain yang menjadi kosong.

Contoh pencatatan:

| Variable | Domain Sebelum | Domain Sesudah | Pruning |
|----------|----------------|----------------|---------|
| INC001 | 3 | dicatat saat pengujian | dicatat |
| INC002 | 4 | dicatat saat pengujian | dicatat |
| INC003 | 4 | dicatat saat pengujian | dicatat |

Nilai pada tabel diisi berdasarkan hasil eksekusi program.

## 5. Pengujian Backtracking

Pengujian Backtracking dilakukan setelah proses AC-3.

Backtracking digunakan untuk mencari complete assignment yang tetap memenuhi constraint.

Hal yang diamati:

1. Variable yang dipilih.
2. Nilai domain yang dicoba.
3. Assignment yang diterima.
4. Assignment yang ditolak.
5. Jumlah backtrack.
6. Status akhir apakah masalah berhasil diselesaikan atau tidak.

## 6. Pengujian MRV

MRV digunakan untuk memilih variable dengan jumlah nilai domain paling sedikit.

Contoh kondisi:

    INC006 → 2 nilai
    INC005 → 4 nilai
    INC007 → 7 nilai

Pada kondisi tersebut, MRV memilih INC006 karena mempunyai jumlah nilai domain paling sedikit.

Pengujian dilakukan untuk memastikan variable yang dipilih sesuai dengan jumlah domain yang tersedia pada saat proses pencarian.

## 7. Pengujian LCV

LCV digunakan untuk menentukan urutan nilai yang akan dicoba dari domain suatu variable.

Nilai yang paling sedikit membatasi variable lain akan dicoba terlebih dahulu.

Pengujian dilakukan dengan melihat urutan nilai yang dipilih oleh solver dan pengaruhnya terhadap domain variable lain.

## 8. Pengujian Validasi Assignment

Setiap hasil assignment perlu diperiksa kembali menggunakan constraint yang telah ditentukan.

Assignment dinyatakan valid apabila:

1. Skill teknisi sesuai dengan kategori insiden.
2. Teknisi tersedia pada slot yang digunakan.
3. Tidak ada teknisi yang menangani dua insiden pada slot yang sama.

Contoh hasil valid:

    INC001 → (TECH004, SLOT_1)
    INC010 → (TECH004, SLOT_2)

Contoh hasil tidak valid:

    INC001 → (TECH004, SLOT_1)
    INC010 → (TECH004, SLOT_1)

## 9. Sensitivity Analysis

Sensitivity analysis digunakan untuk melihat pengaruh perubahan ukuran masalah terhadap proses penyelesaian CSP.

Ukuran masalah dapat dibuat bertahap berdasarkan jumlah insiden yang digunakan.

Contoh ukuran pengujian:

| Ukuran Masalah | Jumlah Insiden |
|----------------|----------------|
| Kecil | 4 |
| Sedang | 8 |
| Besar | 12 |

Pengujian dilakukan menggunakan data yang tersedia pada dataset dan dapat menggunakan subset data untuk ukuran yang lebih kecil.

Untuk setiap ukuran masalah, dicatat beberapa metrik.

### 9.1 Runtime

Runtime digunakan untuk mengukur waktu yang diperlukan solver untuk menyelesaikan CSP.

Satuan waktu dapat menggunakan milidetik (ms).

### 9.2 Jumlah Revisi atau Pruning AC-3

Metrik ini menunjukkan jumlah proses revisi atau pengurangan nilai domain yang dilakukan oleh AC-3.

Semakin banyak nilai domain yang dihapus, semakin besar jumlah pruning yang dilakukan.

### 9.3 Jumlah Backtrack

Jumlah backtrack menunjukkan berapa kali algoritma Backtracking harus kembali ke assignment sebelumnya karena pilihan yang dicoba tidak dapat menghasilkan solusi.

### 9.4 Status Penyelesaian

Status digunakan untuk menunjukkan apakah CSP berhasil diselesaikan atau tidak.

Contoh:

    SOLVED
    UNSATISFIABLE

## 10. Tabel Rancangan Sensitivity Analysis

| Ukuran | Jumlah Insiden | Runtime | AC-3 Revisions/Pruning | Backtracks | Status |
|--------|----------------|---------|-------------------------|------------|--------|
| Kecil | 4 | dicatat saat pengujian | dicatat | dicatat | dicatat |
| Sedang | 8 | dicatat saat pengujian | dicatat | dicatat | dicatat |
| Besar | 12 | dicatat saat pengujian | dicatat | dicatat | dicatat |

Nilai runtime, jumlah pruning, dan jumlah backtrack diisi berdasarkan hasil eksekusi program.

## 11. Ringkasan Skenario Pengujian

| No | Skenario | Tujuan | Hasil yang Diharapkan |
|----|----------|--------|-----------------------|
| 1 | Kondisi normal | Menguji CSP pada kondisi normal | Assignment valid ditemukan |
| 2 | Skill tidak sesuai | Menguji skill constraint | Assignment ditolak |
| 3 | Teknisi tidak tersedia | Menguji availability constraint | Assignment ditolak |
| 4 | Konflik teknisi-slot | Menguji binary constraint | Assignment konflik ditolak |
| 5 | Domain berkurang setelah AC-3 | Menguji pruning | Domain dapat berkurang |
| 6 | Domain kosong | Menguji empty domain | Kondisi gagal terdeteksi |
| 7 | Tidak memiliki solusi | Menguji unsatisfiable CSP | Sistem menyatakan tidak ada solusi |

## 12. Kriteria Keberhasilan

Pengujian dianggap berhasil apabila:

1. Assignment yang memenuhi seluruh constraint dapat diterima.
2. Assignment dengan skill yang tidak sesuai dapat ditolak.
3. Assignment dengan teknisi yang tidak tersedia dapat ditolak.
4. Konflik teknisi dan slot dapat terdeteksi.
5. AC-3 dapat melakukan pruning terhadap domain.
6. Domain kosong dapat terdeteksi.
7. CSP yang tidak memiliki solusi dapat dikenali.
8. Backtracking dapat mencari complete assignment ketika solusi tersedia.
9. MRV dapat memilih variable berdasarkan domain yang paling sedikit.
10. LCV dapat digunakan untuk menentukan urutan nilai yang dicoba.
11. Metrik runtime, jumlah pruning/revisi AC-3, jumlah backtrack, dan status penyelesaian dapat dicatat untuk sensitivity analysis.

## 13. Kesimpulan

Rancangan pengujian Milestone 2 mencakup pengujian kondisi normal, pelanggaran skill, ketidaktersediaan teknisi, konflik teknisi-slot, pruning menggunakan AC-3, domain kosong, dan kondisi CSP yang tidak memiliki solusi.

Selain pengujian fungsional, dilakukan sensitivity analysis dengan beberapa ukuran masalah untuk mengamati runtime, jumlah revisi atau pruning AC-3, jumlah backtrack, dan status penyelesaian.

Hasil pengujian nantinya digunakan untuk memastikan bahwa formulasi CSP dan algoritma yang digunakan dapat menghasilkan assignment teknisi dan slot yang memenuhi constraint yang telah ditentukan.ss