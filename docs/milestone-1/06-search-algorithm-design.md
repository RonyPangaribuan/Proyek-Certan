# Search Algorithm Design

## 1. Keputusan Algoritma

Milestone 1 menggunakan **Uniform Cost Search (UCS)** sebagai Baseline Search
resmi dan **First In, First Out (FIFO)** sebagai metode pembanding tambahan
non-search. Keputusan ini
menggantikan rancangan awal yang masih mempertimbangkan UCS dan A*. A* tidak
diimplementasikan karena milestone ini belum membutuhkan atau menetapkan
heuristic.

UCS dipilih karena seluruh step cost nonnegatif dan UCS mengeluarkan state
dengan cumulative path cost terkecil terlebih dahulu. Goal pertama yang
dikeluarkan dari priority queue merupakan solusi optimal.

## 2. Input dan Importance Score

Input adalah satu snapshot insiden sintetis tervalidasi. Lima komponen numerik
dinormalisasi per batch dan digabungkan dengan bobot berikut:

| Komponen | Bobot |
|---|---:|
| `urgency` | 0.30 |
| `impact` | 0.25 |
| `service_criticality` | 0.20 |
| `affected_users` | 0.15 |
| `waiting_time_min` | 0.10 |

Bobot tersebut dapat dikonfigurasi, tetapi harus nonnegatif dan berjumlah
`1.0`. Bobot adalah asumsi baseline prototype dan belum dikalibrasi menggunakan
data operasional.

Waiting time berada di dalam importance score sebagai mekanisme *aging*.
`category` dan `location` tidak menjadi komponen numerik.

## 3. Cost Function

Saat insiden `i` dipilih setelah `elapsed_time` menit:

```text
completion_time_i = elapsed_time + estimated_handling_time_min_i
step_cost_i        = importance_score_i × completion_time_i
```

Total cost urutan `π` adalah:

```text
C(π) = Σ importance_score_i × completion_time_i
```

Formula ini memberi penalti lebih besar ketika insiden dengan importance tinggi
selesai lebih lambat. Nilainya merupakan *weighted-minute penalty*, bukan biaya
finansial. UCS dan FIFO menggunakan evaluator yang sama agar perbandingannya adil.

## 4. Uniform Cost Search

Priority queue menyimpan tuple berikut:

```text
(cumulative_cost, tie_breaker, sequence, remaining, elapsed_time)
```

Pseudocode:

```text
frontier ← heap berisi initial state dengan cost 0
best_cost[seluruh incident_id] ← 0

while frontier tidak kosong:
    state ← pop state dengan cumulative_cost terkecil

    jika state lebih mahal daripada best_cost[state.remaining]:
        lanjutkan

    jika state.remaining kosong:
        kembalikan state sebagai solusi optimal

    hitung state sebagai expanded

    untuk setiap incident_id dalam state.remaining secara terurut:
        hitung completion_time, step_cost, dan next_cost
        buat next_remaining

        jika next_cost lebih kecil dari best_cost[next_remaining]:
            simpan next_cost
            push successor dengan counter tie-breaker baru
```

Persyaratan penting implementasi:

- menggunakan `heapq`, bukan sorting biasa;
- goal test dilakukan setelah `heappop`;
- counter mencegah Python membandingkan objek state;
- successor dihasilkan menurut `incident_id` agar deterministik;
- state goal tidak dihitung sebagai state yang diperluas;
- hasil memuat urutan, biaya, jumlah state diperluas, dan waktu eksekusi.

## 5. Dominance

State dengan `remaining` yang sama telah menangani subset insiden yang sama.
Jumlah handling time subset tersebut sama untuk semua urutan, sehingga future
cost dari state-state itu dimulai pada elapsed time yang sama. Hanya state
dengan cumulative cost terendah yang perlu dipertahankan.

Pruning ini menghindari perluasan jalur yang terdominasi tanpa mengubah solusi
optimal.

## 6. Pembanding FIFO (Non-search)

FIFO mengurutkan insiden dengan:

```text
waiting_time_min menurun, kemudian incident_id menaik
```

Nilai waiting time terbesar berarti laporan sudah menunggu paling lama dan
dipandang datang paling awal. Setelah urutan terbentuk, setiap completion time,
step cost, dan total cost dihitung menggunakan evaluator yang sama dengan UCS.
FIFO tidak melakukan pencarian dan tidak menggantikan Baseline Search UCS.

## 7. Keluaran dan Evaluasi

CLI menampilkan:

- kontribusi setiap komponen importance score;
- urutan, completion time, dan step cost UCS;
- total cost, jumlah state diperluas, dan waktu eksekusi UCS;
- urutan dan cost FIFO;
- selisih `FIFO - UCS`; dan
- persentase pengurangan biaya jika total cost FIFO lebih besar dari nol.

Optimalitas UCS diuji terhadap brute-force oracle pada batch kecil. Oracle
hanya berada di test dan tidak digunakan oleh implementasi utama.

## 8. Kompleksitas dan Batasan

Masalah mempunyai hingga `n!` urutan lengkap. Dengan dominance berdasarkan
subset, implementasi menyimpan paling banyak orde `2^n` state unik dan
mempertimbangkan hingga orde `n × 2^n` transition. UCS tetap ditujukan untuk
batch prototype kecil, bukan antrean operasional berskala besar.

Sistem memproses snapshot statis dalam satu antrean, menggunakan data sintetis,
dan hanya memberikan rekomendasi. Sistem tidak melakukan monitoring real-time,
diagnosis, troubleshooting, penugasan teknisi, atau perbaikan jaringan.
