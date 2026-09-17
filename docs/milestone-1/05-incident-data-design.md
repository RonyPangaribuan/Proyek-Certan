# Incident Data Design

## 1. Tujuan Data

Data insiden digunakan untuk merepresentasikan berbagai laporan gangguan jaringan kampus yang akan diproses oleh sistem pendukung keputusan. Data tersebut menjadi dasar bagi sistem untuk membandingkan karakteristik beberapa insiden dan menentukan urutan prioritas penanganan.

Pada Milestone 1, data yang digunakan merupakan **data sintetis**, yaitu data yang dibuat oleh tim untuk mensimulasikan kondisi insiden jaringan kampus. Data sintetis yang digunakan dalam prototype bukan merupakan data operasional asli kampus dan tidak menggunakan data sensitif jaringan IT Del.

Penggunaan data sintetis bertujuan untuk:

* mendukung pengembangan prototype;
* melakukan pengujian terhadap rancangan algoritma pencarian;
* memastikan terdapat variasi kondisi insiden yang dapat digunakan dalam pengujian;
* memungkinkan pengembangan sistem sebelum tersedia data operasional aktual.

Data dirancang agar dapat merepresentasikan beberapa karakteristik insiden seperti tingkat urgensi, dampak, jumlah pengguna terdampak, kekritisan layanan, waktu tunggu, dan estimasi waktu penanganan. Atribut tersebut telah disesuaikan dengan kebutuhan prioritisasi yang ditetapkan pada problem framing dan project scope.

---

## 2. Sumber dan Karakteristik Data

Data pada Milestone 1 berasal dari skenario sintetis yang dibuat oleh tim. Skenario tersebut digunakan untuk menggambarkan kondisi yang mungkin terjadi dalam penanganan insiden jaringan kampus tanpa menggunakan data jaringan operasional sebenarnya.

Karakteristik data yang digunakan adalah:

1. Data bersifat sintetis dan digunakan untuk kebutuhan prototype.
2. Setiap insiden memiliki `incident_id` yang unik.
3. Atribut numerik seperti `urgency`, `impact`, dan `service_criticality` menggunakan skala diskrit 1–5.
4. `affected_users` menunjukkan perkiraan jumlah pengguna yang terdampak.
5. `waiting_time_min` menunjukkan lama waktu sebuah laporan telah menunggu penanganan.
6. `estimated_handling_time_min` menunjukkan perkiraan waktu yang diperlukan untuk menangani sebuah insiden.
7. Data tidak berasal dari monitoring jaringan secara real-time.
8. Data dirancang agar memiliki variasi tingkat urgensi, dampak, jumlah pengguna, kekritisan layanan, dan waktu tunggu.

---

## 3. Struktur Data / Data Dictionary

Data insiden menggunakan sembilan atribut utama sebagai berikut.

| Field                         | Type    | Range/Format                            | Contoh         | Keterangan                                    |
| ----------------------------- | ------- | --------------------------------------- | -------------- | --------------------------------------------- |
| `incident_id`                 | String  | `INCxxx`                                | `INC001`       | ID unik untuk setiap insiden                  |
| `category`                    | String  | Kategori gangguan yang telah ditentukan | `wifi_slow`    | Jenis gangguan jaringan                       |
| `location`                    | String  | Nama lokasi atau layanan terdampak      | `Laboratorium` | Lokasi atau layanan yang mengalami gangguan   |
| `urgency`                     | Integer | 1–5                                     | `4`            | Tingkat kebutuhan penanganan segera           |
| `impact`                      | Integer | 1–5                                     | `4`            | Besarnya dampak yang ditimbulkan oleh insiden |
| `affected_users`              | Integer | ≥ 0                                     | `40`           | Perkiraan jumlah pengguna yang terdampak      |
| `service_criticality`         | Integer | 1–5                                     | `4`            | Tingkat kepentingan atau kekritisan layanan   |
| `waiting_time_min`            | Integer | ≥ 0                                     | `15`           | Lama laporan menunggu dalam satuan menit      |
| `estimated_handling_time_min` | Integer | > 0                                     | `30`           | Perkiraan waktu penanganan dalam satuan menit |

---

## 4. Definisi Setiap Atribut

### 4.1 `incident_id`

`incident_id` merupakan identitas unik yang digunakan untuk membedakan setiap laporan insiden.

Format yang digunakan adalah `INCxxx`.

Contoh:

```text
INC001
INC002
INC003
```

Setiap ID harus berbeda dan tidak boleh digunakan oleh lebih dari satu insiden.

---

### 4.2 `category`

`category` menunjukkan jenis gangguan jaringan yang dilaporkan.

Kategori yang dapat digunakan pada prototype antara lain:

* `wifi_slow`
* `wifi_down`
* `network_down`
* `router_failure`
* `access_point_failure`
* `dns_issue`
* `gateway_unreachable`
* `unstable_connection`

Kategori tersebut digunakan untuk memberikan informasi mengenai jenis insiden, bukan untuk melakukan deteksi gangguan secara otomatis.

---

### 4.3 `location`

`location` menunjukkan lokasi atau layanan yang terdampak oleh insiden.

Contoh:

* Ruang Kelas
* Laboratorium
* Perpustakaan
* Asrama
* Ruang Administrasi
* Gedung Perkuliahan
* Layanan Akademik

Atribut ini membantu menggambarkan konteks insiden dan area yang mengalami dampak.

---

### 4.4 `urgency`

`urgency` menunjukkan seberapa mendesak suatu insiden perlu mendapatkan penanganan.

Nilai menggunakan skala 1–5.

| Nilai | Makna                            |
| ----: | -------------------------------- |
|     1 | Sangat rendah atau dapat ditunda |
|     2 | Rendah                           |
|     3 | Sedang                           |
|     4 | Tinggi                           |
|     5 | Sangat mendesak atau kritis      |

Semakin tinggi nilai urgency, semakin besar kebutuhan untuk mempertimbangkan insiden tersebut dalam prioritas penanganan.

---

### 4.5 `impact`

`impact` menunjukkan besarnya dampak yang ditimbulkan oleh suatu insiden terhadap pengguna atau aktivitas yang terdampak.

Nilai menggunakan skala 1–5.

| Nilai | Makna               |
| ----: | ------------------- |
|     1 | Dampak sangat kecil |
|     2 | Dampak kecil        |
|     3 | Dampak sedang       |
|     4 | Dampak besar        |
|     5 | Dampak sangat besar |

Nilai impact digunakan sebagai salah satu informasi untuk membandingkan tingkat kepentingan antarinsiden.

---

### 4.6 `affected_users`

`affected_users` menunjukkan perkiraan jumlah pengguna yang terkena dampak dari suatu insiden.

Contoh nilai:

```text
10
25
40
80
120
```

Nilai harus berupa bilangan bulat dan tidak boleh negatif.

Atribut ini memberikan gambaran mengenai luas dampak insiden dari sisi jumlah pengguna.

---

### 4.7 `service_criticality`

`service_criticality` menunjukkan seberapa penting layanan atau fungsi yang terdampak bagi aktivitas kampus.

Nilai menggunakan skala 1–5.

| Nilai | Makna                             |
| ----: | --------------------------------- |
|     1 | Layanan tidak kritis              |
|     2 | Layanan dengan kepentingan rendah |
|     3 | Layanan cukup penting             |
|     4 | Layanan penting                   |
|     5 | Layanan sangat kritis             |

Sebagai contoh, layanan yang mendukung aktivitas akademik utama dapat memiliki tingkat criticality yang lebih tinggi dibandingkan layanan yang tidak terlalu penting terhadap aktivitas utama.

---

### 4.8 `waiting_time_min`

`waiting_time_min` menunjukkan berapa lama laporan insiden telah menunggu sejak diterima sampai kondisi saat data tersebut digunakan.

Satuan yang digunakan adalah menit.

Contoh:

```text
15 menit
35 menit
90 menit
180 menit
```

Nilai tidak boleh negatif.

Waiting time digunakan untuk mempertimbangkan insiden yang telah menunggu lebih lama sehingga tidak terus tertunda ketika terdapat banyak laporan lain.

---

### 4.9 `estimated_handling_time_min`

`estimated_handling_time_min` menunjukkan perkiraan waktu yang diperlukan untuk menangani suatu insiden.

Satuan yang digunakan adalah menit.

Contoh:

```text
15 menit
20 menit
30 menit
45 menit
50 menit
```

Nilai harus lebih besar dari 0.

Atribut ini memberikan informasi mengenai perkiraan beban waktu penanganan suatu insiden.

---

## 5. Contoh Data Sintetis

Berikut merupakan contoh data sintetis yang digunakan untuk merepresentasikan beberapa kondisi insiden jaringan kampus pada Milestone 1.

| ID     | Category             | Location           | Urgency | Impact | Users | Criticality | Waiting | Handling |
| ------ | -------------------- | ------------------ | ------: | -----: | ----: | ----------: | ------: | -------: |
| INC001 | wifi_slow            | Ruang Kelas        |       2 |      2 |    15 |           2 |      35 |       20 |
| INC002 | network_down         | Laboratorium       |       4 |      4 |    40 |           4 |      15 |       30 |
| INC003 | network_down         | Layanan Akademik   |       5 |      5 |   120 |           5 |      10 |       40 |
| INC004 | unstable_connection  | Perpustakaan       |       3 |      3 |    25 |           3 |     180 |       25 |
| INC005 | access_point_failure | Asrama             |       4 |      3 |    60 |           3 |      45 |       35 |
| INC006 | dns_issue            | Ruang Administrasi |       3 |      2 |    30 |           4 |      70 |       20 |
| INC007 | wifi_down            | Gedung Perkuliahan |       4 |      5 |    80 |           4 |      25 |       45 |
| INC008 | router_failure       | Laboratorium       |       5 |      4 |    20 |           4 |       5 |       35 |
| INC009 | gateway_unreachable  | Layanan Akademik   |       5 |      5 |    55 |           5 |      20 |       50 |
| INC010 | wifi_slow            | Perpustakaan       |       2 |      2 |    50 |           2 |     150 |       25 |
| INC011 | unstable_connection  | Ruang Kelas        |       3 |      4 |    10 |           2 |      90 |       15 |
| INC012 | wifi_down            | Asrama             |       4 |      3 |   100 |           3 |      60 |       40 |

Data tersebut sengaja dibuat bervariasi agar algoritma dapat diuji pada kondisi yang berbeda.

Contoh variasi kondisi:

* `INC008` memiliki urgency tinggi tetapi jumlah pengguna terdampak relatif sedikit.
* `INC003` memiliki impact, urgency, dan service criticality yang tinggi dengan jumlah pengguna terdampak besar.
* `INC004` memiliki urgency sedang tetapi waiting time yang cukup lama.
* `INC012` memiliki jumlah pengguna terdampak besar tetapi service criticality tidak berada pada nilai maksimum.
* `INC009` memiliki service criticality sangat tinggi dengan jumlah pengguna terdampak yang lebih rendah dibandingkan `INC003`.
* `INC010` memiliki jumlah pengguna terdampak cukup banyak tetapi urgency dan impact relatif rendah serta waiting time cukup lama.

Variasi tersebut digunakan agar proses pencarian tidak hanya membandingkan insiden berdasarkan satu atribut.

---

## 6. Asumsi Data

Beberapa asumsi yang digunakan dalam perancangan data adalah:

1. Seluruh data pada Milestone 1 merupakan data sintetis.
2. Data sintetis dibuat untuk mensimulasikan kondisi laporan insiden jaringan kampus.
3. `urgency`, `impact`, dan `service_criticality` menggunakan skala 1–5.
4. `affected_users` merupakan estimasi jumlah pengguna yang terdampak.
5. `waiting_time_min` dihitung sejak laporan diterima sampai waktu data digunakan dalam proses keputusan.
6. `estimated_handling_time_min` merupakan perkiraan waktu penanganan.
7. Nilai pada data tidak merepresentasikan kondisi jaringan IT Del yang sebenarnya.
8. Data belum diperoleh dari monitoring jaringan secara real-time.
9. Data digunakan untuk pengembangan prototype dan pengujian algoritma pada Milestone 1.

---

## 7. Validasi Data

Untuk menjaga konsistensi data, digunakan aturan validasi berikut:

| Field                         | Aturan Validasi                          |
| ----------------------------- | ---------------------------------------- |
| `incident_id`                 | Harus unik dan mengikuti format `INCxxx` |
| `category`                    | Tidak boleh kosong                       |
| `location`                    | Tidak boleh kosong                       |
| `urgency`                     | Harus berupa integer dengan nilai 1–5    |
| `impact`                      | Harus berupa integer dengan nilai 1–5    |
| `affected_users`              | Harus berupa integer dengan nilai ≥ 0    |
| `service_criticality`         | Harus berupa integer dengan nilai 1–5    |
| `waiting_time_min`            | Harus berupa integer dengan nilai ≥ 0    |
| `estimated_handling_time_min` | Harus berupa integer dengan nilai > 0    |

Validasi diperlukan agar data yang digunakan dalam proses pencarian memiliki format dan rentang nilai yang konsisten.

---

## 8. Keterkaitan Data dengan Prioritisasi

Atribut dalam data dirancang untuk memberikan informasi yang diperlukan sistem dalam membandingkan beberapa insiden.

Insiden dengan urgency, impact, jumlah pengguna terdampak, dan service criticality yang tinggi dapat memiliki konsekuensi yang lebih besar apabila penanganannya ditunda. Selain itu, waiting time digunakan untuk mempertimbangkan laporan yang telah menunggu lebih lama sehingga tidak terus berada di belakang laporan lain.

`estimated_handling_time_min` menentukan completion time dalam urutan penanganan. Importance score menggunakan bobot baseline `urgency = 0.30`, `impact = 0.25`, `service_criticality = 0.20`, `affected_users = 0.15`, dan `waiting_time = 0.10`. Bobot tersebut merupakan asumsi prototype, bukan hasil kalibrasi data operasional.

Path cost menggunakan *weighted completion penalty*, yaitu `importance_score × completion_time` pada setiap langkah. Waktu tunggu berada di dalam importance score sebagai mekanisme *aging* agar laporan lama tidak terus tertunda.

Dengan demikian, data berfungsi sebagai representasi kondisi insiden yang menjadi input bagi proses pencarian, bukan sebagai keputusan prioritas yang telah ditentukan sebelumnya.

---

## 9. Kesimpulan

Desain data pada Milestone 1 menggunakan data sintetis untuk merepresentasikan laporan insiden jaringan kampus secara terstruktur. Sembilan atribut yang digunakan menggambarkan identitas, jenis, lokasi, urgensi, dampak, jumlah pengguna terdampak, kekritisan layanan, waktu tunggu, dan estimasi waktu penanganan. Data tersebut menjadi dasar Baseline Search UCS dalam mencari urutan dengan weighted-minute penalty minimum, sedangkan FIFO hanya menjadi metode pembanding tambahan non-search.
