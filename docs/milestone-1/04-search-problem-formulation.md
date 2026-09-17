# Search Problem Formulation

## A. Overview

Pada Milestone 1, prioritisasi insiden jaringan diformulasikan sebagai masalah
pencarian urutan. **Uniform Cost Search (UCS)** merupakan Baseline Search resmi,
sedangkan **First In, First Out (FIFO)** hanya menjadi metode pembanding tambahan
non-search. A* tidak diimplementasikan pada tahap ini.

Sistem memproses satu batch atau snapshot data sintetis. Output merupakan
rekomendasi urutan penanganan; keputusan akhir tetap berada pada administrator
jaringan.

## B. Incident Importance Score

Untuk batch dengan maksimum jumlah pengguna `max_affected_users` dan maksimum
waktu tunggu `max_waiting_time`, normalisasi ditetapkan sebagai:

```text
normalized_urgency     = urgency / 5
normalized_impact      = impact / 5
normalized_criticality = service_criticality / 5
normalized_users       = affected_users / max_affected_users
normalized_waiting     = waiting_time_min / max_waiting_time
```

Jika salah satu maksimum bernilai nol, nilai normalisasi komponen tersebut
ditetapkan menjadi nol.

```text
importance_score =
    0.30 × normalized_urgency
  + 0.25 × normalized_impact
  + 0.20 × normalized_criticality
  + 0.15 × normalized_users
  + 0.10 × normalized_waiting
```

Seluruh bobot nonnegatif dan berjumlah `1.0`. Bobot ini adalah asumsi baseline
prototype, bukan hasil kalibrasi data operasional. `category` dan `location`
menjadi konteks dan tidak masuk ke formula numerik.

Waktu tunggu dimasukkan sebagai mekanisme *aging*. Dengan demikian, laporan
yang sudah lama menunggu memperoleh tambahan tingkat kepentingan dan tidak
terus tertunda oleh laporan baru.

## C. Formulasi Formal (X, A, T, G, C)

| Simbol | Definisi dalam proyek |
|---|---|
| `X` | State `(sequence, remaining, elapsed_time, total_cost)` yang merepresentasikan urutan parsial. |
| `A(x)` | Memilih satu insiden dari `remaining` sebagai insiden berikutnya. |
| `T(x, a)` | Menambahkan insiden terpilih ke `sequence`, menghapusnya dari `remaining`, lalu memperbarui elapsed time dan total cost. |
| `G` | Goal tercapai ketika `remaining` kosong dan seluruh insiden berada dalam `sequence`. |
| `C` | Jumlah `importance_score_i × completion_time_i` sepanjang jalur. |

## D. State Space (X)

Satu state terdiri dari:

- `sequence`: tuple ID insiden yang telah dipilih;
- `remaining`: tuple ID insiden yang belum dipilih;
- `elapsed_time`: total estimasi waktu penanganan dalam `sequence`;
- `total_cost`: biaya kumulatif `sequence`.

State dibentuk menggunakan ID insiden yang terurut agar ekspansi deterministik.

## E. Initial State

```text
sequence     = ()
remaining    = seluruh incident_id
elapsed_time = 0
total_cost   = 0
```

## F. Action (A) dan Transition (T)

Action memilih satu insiden `i` dari `remaining` sebagai insiden berikutnya.
Transition menghasilkan:

```text
new_sequence     = sequence + (i,)
new_remaining    = remaining - {i}
completion_time  = elapsed_time + estimated_handling_time_min_i
step_cost        = importance_score_i × completion_time
new_elapsed_time = completion_time
new_total_cost   = total_cost + step_cost
```

Importance score berada pada rentang 0–1 dan handling time bernilai positif,
sehingga seluruh step cost nonnegatif.

## G. Goal Test (G)

Goal tercapai ketika `remaining` kosong dan seluruh insiden sudah berada dalam
`sequence`. Sesuai UCS, goal test dilakukan ketika state dikeluarkan dari
priority queue, bukan ketika state pertama kali dimasukkan.

## H. Path Cost (C)

Untuk urutan insiden `π`, digunakan *weighted completion penalty*:

```text
C(π) = Σ importance_score_i × completion_time_i
```

Completion time mencakup waktu penanganan seluruh insiden yang ditempatkan
sebelum dan termasuk insiden `i`. Akibatnya, menempatkan insiden penting terlalu
belakang menghasilkan penalti lebih besar. Nilai ini memiliki interpretasi
*weighted-minute penalty* atau penalti menit terbobot, bukan biaya finansial.

## I. Dominance dan Determinisme

Dua jalur yang mencapai himpunan `remaining` yang sama telah menangani himpunan
insiden yang sama. Karena total handling time himpunan tersebut tidak bergantung
pada urutannya, keduanya memiliki `elapsed_time` yang sama. Jalur dengan
`total_cost` lebih tinggi terdominasi dan tidak perlu diperluas.

Implementasi menyimpan biaya terbaik untuk setiap tuple `remaining`, memakai
counter sebagai tie-breaker heap, dan menghasilkan successor berdasarkan
`incident_id`. Input yang sama karena itu menghasilkan urutan yang sama.

## J. Pembanding FIFO (Non-search)

FIFO menempatkan laporan yang datang lebih awal terlebih dahulu. Karena
`waiting_time_min` menyatakan lamanya laporan sudah menunggu, urutan FIFO adalah:

1. `waiting_time_min` terbesar lebih dahulu;
2. `incident_id` menaik sebagai tie-breaker.

Biaya FIFO dihitung dengan fungsi weighted completion penalty yang sama dengan
UCS agar perbandingan adil. FIFO tidak diposisikan sebagai algoritma pencarian
atau pengganti Baseline Search UCS.

## K. Batasan Formulasi

- Data bersifat sintetis dan statis selama pencarian.
- Penanganan dimodelkan sebagai satu antrean tanpa paralelisme atau penugasan
  teknisi.
- UCS mempunyai kompleksitas eksponensial terhadap jumlah insiden; dominance
  mengurangi state efektif menjadi kombinasi subset, tetapi tidak mengubah
  batasan skalabilitas dasarnya.
- Sistem tidak melakukan diagnosis atau tindakan perbaikan jaringan.
