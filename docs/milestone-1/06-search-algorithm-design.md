06-search-algorithm-design.md
# Search Algorithm Design

## 1. Tujuan Algoritma

Algoritma pencarian digunakan untuk membantu sistem menentukan urutan penanganan dari beberapa laporan insiden jaringan.

Masalah yang dihadapi adalah terdapat beberapa insiden dengan karakteristik yang berbeda. Oleh karena itu, sistem tidak hanya menentukan urutan berdasarkan waktu laporan masuk, tetapi mencari urutan penanganan dengan mempertimbangkan penalty atau cost yang dihasilkan dari urutan tersebut.

Tujuan rancangan algoritma adalah mencari urutan penanganan insiden yang menghasilkan total penalty/cost serendah mungkin berdasarkan kriteria yang telah ditentukan.

Pada Milestone 1, algoritma yang dipertimbangkan adalah **Uniform Cost Search (UCS)** dan **A***.

Algoritma tersebut digunakan sebagai mekanisme decision support. Hasil algoritma berupa rekomendasi urutan penanganan, sedangkan keputusan akhir tetap berada pada pihak yang bertanggung jawab terhadap operasional jaringan.

---

## 2. Baseline FIFO

Sebelum menggunakan algoritma search, salah satu pendekatan sederhana yang dapat digunakan sebagai pembanding adalah **First In, First Out (FIFO)**.

FIFO menangani insiden berdasarkan urutan laporan diterima. Artinya, laporan yang masuk lebih dahulu akan ditempatkan lebih dahulu dalam urutan penanganan.

Contoh:

```text
08.00 → INC001 → WiFi lambat
08.05 → INC002 → Gangguan layanan akademik
08.10 → INC003 → Gangguan jaringan laboratorium
```

Dengan FIFO, urutannya menjadi:

```text
INC001 → INC002 → INC003
```

Pendekatan ini sederhana, tetapi tidak mempertimbangkan perbedaan karakteristik dan tingkat kepentingan setiap insiden.

Sebagai contoh, apabila INC001 merupakan gangguan WiFi dengan dampak kecil, sedangkan INC002 merupakan gangguan layanan akademik yang sangat kritis, maka urutan FIFO tetap menempatkan INC001 lebih dahulu hanya karena laporan tersebut masuk lebih awal.

Kondisi tersebut menjadi alasan perlunya mekanisme prioritisasi yang mempertimbangkan karakteristik insiden.

FIFO dapat digunakan sebagai **baseline pembanding**, bukan sebagai mekanisme utama yang ingin dikembangkan.

---

## 3. Hubungan dengan Search Problem

Masalah prioritisasi direpresentasikan sebagai search problem. Setiap state menggambarkan kondisi urutan penanganan yang telah dibentuk sampai suatu tahap.

Komponen search problem yang digunakan adalah:

| Komponen         | Definisi dalam Proyek                                                  |
| ---------------- | ---------------------------------------------------------------------- |
| State            | Kondisi urutan penanganan sementara dari insiden yang telah dipilih    |
| Initial State    | Kondisi ketika belum ada insiden yang ditempatkan dalam urutan         |
| Action           | Memilih satu insiden yang belum ditempatkan sebagai insiden berikutnya |
| Transition Model | Menambahkan insiden yang dipilih ke urutan penanganan sementara        |
| Goal             | Seluruh insiden telah ditempatkan dalam suatu urutan                   |
| Path Cost        | Total penalty/cost yang dihasilkan dari urutan penanganan sementara    |

Contoh sederhana:

```text
Initial State
[]
```

Action:

```text
Memilih INC001
```

menjadi:

```text
[INC001]
```

Kemudian memilih INC003:

```text
[INC001, INC003]
```

Kemudian memilih INC002:

```text
[INC001, INC003, INC002]
```

Ketika seluruh insiden telah ditempatkan, state tersebut memenuhi kondisi goal.

Dengan model tersebut, algoritma dapat membandingkan berbagai kemungkinan urutan penanganan.

---

## 4. Uniform Cost Search (UCS)

Uniform Cost Search merupakan algoritma pencarian yang memilih state dengan cumulative path cost paling rendah untuk dieksplorasi terlebih dahulu.

UCS menggunakan **priority queue** untuk menyimpan kandidat state berdasarkan cost.

Cost kumulatif dapat direpresentasikan sebagai:

```text
g(n) = cumulative path cost
```

Pada setiap tahap pencarian, state dengan nilai `g(n)` paling rendah akan diprioritaskan untuk dieksplorasi.

Secara konseptual:

```text
State A → g(n) = 20
State B → g(n) = 15
State C → g(n) = 30
```

UCS akan mengeksplorasi:

```text
State B
```

lebih dahulu karena memiliki cumulative cost paling rendah.

Dalam konteks proyek ini, setiap state merepresentasikan urutan penanganan sementara. Setiap action menambahkan satu insiden ke dalam urutan tersebut. Cost kemudian menunjukkan penalty yang dihasilkan oleh keputusan penempatan insiden tersebut.

Proses pencarian dilanjutkan sampai ditemukan state yang memenuhi goal, yaitu seluruh insiden telah ditempatkan dalam urutan.

UCS sesuai untuk dijadikan baseline karena dapat bekerja berdasarkan path cost tanpa membutuhkan heuristic tambahan.

---

## 5. Path Cost / Penalty

Path cost merupakan bagian penting dalam rancangan algoritma karena cost harus menggambarkan konsekuensi dari urutan penanganan.

Cost tidak dimaksudkan sebagai "semakin penting insiden maka semakin besar cost ketika dipilih". Sebaliknya, cost digunakan untuk menggambarkan **penalty atau kerugian akibat sebuah insiden mengalami penundaan dalam urutan penanganan**.

Sebagai contoh, terdapat insiden yang memiliki:

* urgency tinggi;
* impact tinggi;
* jumlah pengguna terdampak besar;
* service criticality tinggi.

Apabila insiden tersebut ditempatkan pada urutan belakang, maka konsekuensi penundaannya dapat lebih besar dibandingkan apabila ditempatkan pada urutan awal.

Faktor yang dapat dipertimbangkan dalam rancangan cost meliputi:

* `urgency`;
* `impact`;
* `affected_users`;
* `service_criticality`;
* `waiting_time_min`;
* `estimated_handling_time_min`.

Pada tahap ini, faktor-faktor tersebut masih merupakan kandidat komponen cost. Bobot dan formula final belum ditetapkan.

---

## 6. Kandidat Incident Importance Score

Salah satu rancangan yang dapat digunakan adalah membuat suatu nilai yang menggambarkan tingkat kepentingan sebuah insiden.

Nilai tersebut dapat disebut sebagai:

```text
incident_importance_score
```

Secara konseptual, nilai tersebut dapat mempertimbangkan:

```text
urgency
impact
affected_users
service_criticality
waiting_time_min
```

Tujuannya adalah menghasilkan representasi tingkat kepentingan yang dapat digunakan dalam perhitungan penalty.

Namun, belum ditentukan formula dan bobot final untuk setiap atribut.

Sebagai contoh konseptual:

```text
incident_importance_score
        ↓
menggambarkan tingkat kepentingan insiden
        ↓
digunakan untuk mempertimbangkan penalty penundaan
```

Apabila pada tahap berikutnya digunakan pembobotan, setiap bobot harus memiliki alasan yang jelas dan dapat dijelaskan berdasarkan kebutuhan prioritisasi.

---

## 7. Konsep Delay Penalty

Prioritas tidak hanya dipengaruhi oleh karakteristik insiden, tetapi juga oleh posisi insiden dalam urutan penanganan.

Misalnya terdapat:

```text
INC001 = tingkat kepentingan rendah
INC002 = tingkat kepentingan tinggi
INC003 = tingkat kepentingan sangat tinggi
```

Jika urutannya:

```text
INC003 → INC002 → INC001
```

maka insiden yang paling penting ditempatkan lebih awal.

Sebaliknya, apabila urutannya:

```text
INC001 → INC002 → INC003
```

maka INC003 mengalami penundaan lebih besar karena ditempatkan pada urutan terakhir.

Secara konseptual, hubungan tersebut dapat ditulis sebagai:

```text
delay_penalty ≈ importance × delay
```

Persamaan tersebut hanya merupakan gambaran konsep dan **bukan formula final proyek**.

Inti konsepnya adalah:

```text
Importance tinggi
       +
Delay tinggi
       ↓
Penalty lebih besar
```

Dengan demikian, algoritma memiliki alasan untuk mencari urutan yang mengurangi penalty akibat penundaan insiden yang lebih penting.

---

## 8. A*

A* merupakan algoritma pencarian yang menggunakan kombinasi antara cost yang telah ditempuh dan estimasi cost yang masih tersisa.

Fungsi evaluasi A* dapat dituliskan sebagai:

```text
f(n) = g(n) + h(n)
```

dengan:

* `g(n)` = cumulative penalty dari urutan yang telah terbentuk;
* `h(n)` = estimasi penalty minimum dari insiden yang belum ditempatkan;
* `f(n)` = estimasi total cost dari state tersebut.

Perbedaan utama dengan UCS adalah A* menggunakan informasi tambahan berupa heuristic.

Secara sederhana:

```text
UCS
f(n) = g(n)

A*
f(n) = g(n) + h(n)
```

Dengan heuristic yang sesuai, A* dapat mengarahkan pencarian menuju state yang diperkirakan memiliki total cost yang lebih baik tanpa harus mengeksplorasi seluruh alternatif secara sama.

---

## 9. Kandidat Heuristic

Heuristic digunakan untuk memperkirakan cost yang masih mungkin muncul dari state saat ini.

Untuk proyek ini, kandidat heuristic secara konseptual adalah:

> estimasi minimum penalty yang masih mungkin dihasilkan oleh insiden yang belum ditempatkan dalam urutan.

Contoh:

```text
State saat ini:
[INC002]

Insiden belum ditempatkan:
INC001
INC003
INC004
```

Maka `h(n)` dapat digunakan untuk memperkirakan penalty minimum yang mungkin muncul dari INC001, INC003, dan INC004 yang masih belum ditempatkan.

Namun, heuristic tersebut masih berupa kandidat konseptual.

Heuristic final harus dianalisis lebih lanjut untuk memastikan sifatnya sesuai dengan kebutuhan A*, terutama jika optimalitas A* akan digunakan sebagai dasar evaluasi.

Pada Milestone 1, heuristic tidak dikunci sebelum dilakukan review bersama tim.

---

## 10. Contoh Perhitungan Manual

Bagian ini menggunakan tiga insiden sebagai contoh sederhana:

| ID     | Urgency | Impact | Users | Criticality | Waiting |
| ------ | ------: | -----: | ----: | ----------: | ------: |
| INC001 |       2 |      2 |    15 |           2 |      35 |
| INC002 |       4 |      4 |    40 |           4 |      15 |
| INC003 |       5 |      5 |   120 |           5 |      10 |

Data tersebut merupakan contoh dari data sintetis pada `05-incident-data-design.md`.

Untuk mempermudah ilustrasi, digunakan **importance score contoh**, bukan formula final.

Misalnya secara ilustratif:

```text
INC001 → importance = rendah
INC002 → importance = tinggi
INC003 → importance = sangat tinggi
```

Kemudian dibandingkan tiga kemungkinan urutan:

### Urutan A

```text
INC001 → INC002 → INC003
```

INC003 ditempatkan pada posisi ketiga sehingga mengalami delay paling besar dalam urutan tersebut.

### Urutan B

```text
INC003 → INC002 → INC001
```

INC003 ditempatkan pertama dan INC002 ditempatkan kedua.

### Urutan C

```text
INC002 → INC003 → INC001
```

INC002 ditempatkan pertama, sedangkan INC003 ditempatkan kedua.

Secara konseptual, apabila penalty ditentukan berdasarkan importance dan delay, maka urutan yang menempatkan insiden dengan importance tinggi terlalu belakang dapat menghasilkan penalty yang lebih besar.

Untuk contoh sederhana:

```text
Urutan A
INC001 → INC002 → INC003
                ↑
       INC003 terlambat

Urutan B
INC003 → INC002 → INC001
  ↑
kritis ditangani lebih awal
```

Perhitungan numerik final belum dilakukan karena formula dan bobot path cost masih harus direview bersama tim.

Contoh ini digunakan untuk menunjukkan bagaimana **posisi dalam urutan dapat memengaruhi penalty**, bukan untuk menetapkan formula cost final.

---

## 11. Perbandingan UCS dan A*

| Aspek                       | UCS                                                     | A*                                                              |
| --------------------------- | ------------------------------------------------------- | --------------------------------------------------------------- |
| Menggunakan `g(n)`          | Ya                                                      | Ya                                                              |
| Menggunakan heuristic       | Tidak                                                   | Ya                                                              |
| Fungsi evaluasi             | `g(n)`                                                  | `g(n) + h(n)`                                                   |
| Optimal jika cost valid     | Ya, dengan asumsi cost memenuhi kondisi yang diperlukan | Ya, dengan heuristic yang sesuai                                |
| Kebutuhan heuristic         | Tidak ada                                               | Ada                                                             |
| Eksplorasi                  | Berdasarkan cumulative cost                             | Berdasarkan cumulative cost dan estimasi cost                   |
| Kemudahan implementasi awal | Lebih sederhana                                         | Lebih kompleks                                                  |
| Cocok sebagai baseline      | Ya                                                      | Dapat digunakan sebagai perbandingan setelah heuristic tersedia |
| Risiko desain tambahan      | Tidak membutuhkan heuristic                             | Memerlukan heuristic yang harus dirancang dengan benar          |

---

## 12. Rekomendasi Sementara

Untuk Milestone 1, **UCS dapat digunakan sebagai baseline awal** karena tidak membutuhkan heuristic dan dapat langsung menggunakan path cost yang dirancang untuk masalah prioritisasi.

A* dapat digunakan sebagai pendekatan pembanding apabila heuristic yang sesuai berhasil dirancang dan dapat dijelaskan sifatnya.

Keputusan mengenai algoritma yang digunakan pada implementasi akhir tetap perlu dilakukan melalui review bersama tim setelah path cost dan kemungkinan heuristic ditetapkan.

---

## 13. Batasan Rancangan Algoritma

Rancangan algoritma pada Milestone 1 memiliki beberapa batasan:

1. Belum terdapat implementasi Python.
2. Path cost final belum ditentukan.
3. Bobot setiap atribut belum ditentukan.
4. Heuristic A* belum ditetapkan sebagai formula final.
5. Data yang digunakan masih berupa data sintetis.
6. Algoritma berfokus pada prioritisasi urutan insiden.
7. Algoritma tidak melakukan troubleshooting jaringan secara otomatis.
8. Algoritma tidak melakukan perbaikan jaringan secara langsung.
9. Algoritma tidak melakukan monitoring jaringan secara real-time.
10. Penugasan teknisi secara penuh belum menjadi fokus implementasi Milestone 1.

Batasan tersebut mengikuti ruang lingkup Milestone 1 yang berfokus pada fondasi masalah, representasi search problem, data awal, dan mekanisme awal prioritisasi.

---

## 14. Kesimpulan

Masalah prioritisasi insiden jaringan dapat direpresentasikan sebagai search problem dengan state berupa urutan penanganan sementara, action berupa pemilihan insiden berikutnya, goal berupa seluruh insiden yang telah ditempatkan dalam urutan, dan path cost berupa penalty dari urutan tersebut.

UCS melakukan pencarian berdasarkan cumulative cost `g(n)`, sedangkan A* menambahkan heuristic melalui fungsi `f(n) = g(n) + h(n)`. Dalam rancangan ini, cost diarahkan untuk menggambarkan konsekuensi penundaan insiden berdasarkan karakteristiknya. Formula, bobot cost, dan heuristic final belum ditetapkan dan akan direview bersama tim sebelum tahap implementasi.
