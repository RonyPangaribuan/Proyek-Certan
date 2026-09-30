# Desain Data dan Constraint Bisnis

## 1. Tujuan

Pada Milestone 2, sistem dikembangkan dari proses prioritisasi insiden pada Milestone 1 menuju proses pembagian tugas penanganan insiden kepada teknisi.

Data teknisi digunakan sebagai input untuk proses Constraint Satisfaction Problem (CSP). Data ini membantu sistem menentukan pasangan teknisi dan slot waktu yang memenuhi aturan yang telah ditentukan.

Data teknisi yang digunakan pada tahap ini merupakan **data sintetis untuk kebutuhan prototipe dan pengujian**, bukan data teknisi atau aturan operasional resmi Institut Teknologi Del.

---

## 2. Data Teknisi

Data teknisi dirancang berdasarkan kebutuhan constraint pada Milestone 2. Atribut yang digunakan adalah:

| Atribut           | Tipe Data       | Keterangan                                                 |
| ----------------- | --------------- | ---------------------------------------------------------- |
| `technician_id`   | String          | ID unik setiap teknisi                                     |
| `skills`          | Array of String | Daftar jenis masalah jaringan yang dapat ditangani teknisi |
| `available_slots` | Array of String | Daftar slot waktu ketika teknisi tersedia                  |

### 2.1 `technician_id`

`technician_id` digunakan sebagai identitas unik setiap teknisi.

Contoh:

```text
TECH001
TECH002
TECH003
```

Setiap teknisi harus mempunyai `technician_id` yang berbeda.

### 2.2 `skills`

`skills` berisi jenis insiden jaringan yang dapat ditangani oleh teknisi.

Jenis skill disesuaikan dengan kategori insiden yang telah digunakan pada Milestone 1, seperti:

* `wifi_slow`
* `wifi_down`
* `network_down`
* `router_failure`
* `access_point_failure`
* `dns_issue`
* `gateway_unreachable`
* `unstable_connection`

Seorang teknisi dapat mempunyai lebih dari satu skill.

### 2.3 `available_slots`

`available_slots` berisi slot waktu ketika teknisi dapat menangani insiden.

Contoh:

```text
SLOT_1
SLOT_2
SLOT_3
```

Slot pada dataset ini merupakan representasi waktu sintetis untuk kebutuhan prototipe.

---

## 3. Constraint Bisnis

Constraint digunakan untuk membatasi assignment agar pasangan teknisi dan slot yang dihasilkan oleh CSP tetap valid.

Constraint yang digunakan pada Milestone 2 adalah:

### 3.1 Constraint Skill

Teknisi harus memiliki skill yang sesuai dengan kategori insiden yang ditangani.

Contoh:

Jika:

```text
Incident = INC001
Category = wifi_down
```

maka teknisi yang dipilih harus memiliki:

```text
wifi_down
```

di dalam daftar `skills`.

**Assignment valid:**

```text
INC001 → TECH001
```

jika `TECH001` memiliki skill `wifi_down`.

**Assignment tidak valid:**

```text
INC001 → TECH002
```

jika `TECH002` tidak memiliki skill `wifi_down`.

Constraint ini memastikan teknisi yang diberikan kepada suatu insiden mempunyai kemampuan yang sesuai dengan jenis masalah tersebut.

---

### 3.2 Constraint Ketersediaan Teknisi

Teknisi hanya dapat diberikan kepada insiden pada slot yang terdapat di dalam `available_slots` teknisi tersebut.

Contoh:

```text
TECH001
available_slots = [SLOT_1, SLOT_3]
```

Maka:

```text
INC001 → (TECH001, SLOT_1)
```

merupakan assignment valid.

Sedangkan:

```text
INC001 → (TECH001, SLOT_2)
```

merupakan assignment tidak valid karena `TECH001` tidak tersedia pada `SLOT_2`.

---

### 3.3 Constraint Konflik Teknisi dan Slot

Satu teknisi tidak boleh menangani dua insiden pada slot yang sama.

Contoh assignment:

```text
INC001 → (TECH001, SLOT_1)
INC002 → (TECH001, SLOT_1)
```

merupakan assignment tidak valid karena `TECH001` mendapatkan dua insiden pada slot yang sama.

Sebaliknya:

```text
INC001 → (TECH001, SLOT_1)
INC002 → (TECH001, SLOT_2)
```

dapat menjadi assignment valid karena teknisi yang sama berada pada slot yang berbeda.

Constraint ini digunakan untuk mencegah satu teknisi mendapatkan dua tugas yang harus dilakukan pada waktu yang sama.

---

## 4. Contoh Assignment Valid

Berikut contoh assignment yang memenuhi constraint:

```text
INC001 → (TECH001, SLOT_1)
INC002 → (TECH002, SLOT_1)
INC003 → (TECH001, SLOT_2)
```

Assignment tersebut valid apabila:

1. `TECH001` memiliki skill yang sesuai dengan `INC001` dan `INC003`.
2. `TECH002` memiliki skill yang sesuai dengan `INC002`.
3. `TECH001` tersedia pada `SLOT_1` dan `SLOT_2`.
4. `TECH002` tersedia pada `SLOT_1`.
5. Tidak ada teknisi yang mendapatkan dua insiden pada slot yang sama.

---

## 5. Contoh Assignment Tidak Valid

### Kasus 1 – Skill Tidak Sesuai

```text
INC001 → (TECH002, SLOT_1)
```

Tidak valid apabila `TECH002` tidak memiliki skill yang sesuai dengan kategori `INC001`.

---

### Kasus 2 – Teknisi Tidak Tersedia

```text
INC001 → (TECH001, SLOT_2)
```

Tidak valid apabila `SLOT_2` tidak terdapat pada `available_slots` milik `TECH001`.

---

### Kasus 3 – Konflik Teknisi dan Slot

```text
INC001 → (TECH001, SLOT_1)
INC002 → (TECH001, SLOT_1)
```

Tidak valid karena `TECH001` ditugaskan kepada dua insiden pada slot yang sama.

---

## 6. Hubungan dengan CSP

Data teknisi dan constraint pada bagian ini akan digunakan sebagai dasar formulasi CSP pada Milestone 2.

Setiap insiden akan menjadi variable yang harus diberikan sebuah nilai berupa pasangan:

```text
(teknisi, slot)
```

Domain setiap insiden berisi kemungkinan pasangan teknisi dan slot yang memenuhi constraint dasar.

Contoh:

```text
INC001:
[
  (TECH001, SLOT_1),
  (TECH001, SLOT_3),
  (TECH003, SLOT_2)
]
```

Pasangan yang tidak memenuhi constraint skill atau ketersediaan tidak dimasukkan ke domain.

Constraint konflik teknisi-slot kemudian digunakan untuk memastikan dua insiden tidak mendapatkan teknisi yang sama pada slot yang sama.

Formulasi formal `Variables`, `Domains`, dan `Constraints` akan dijelaskan lebih lanjut pada dokumen formulasi CSP.

---

## 7. Asumsi Prototipe

Data dan aturan pada desain ini menggunakan beberapa asumsi:

1. Data teknisi merupakan data sintetis yang dibuat untuk kebutuhan prototype dan pengujian.
2. `technician_id` bersifat unik untuk setiap teknisi.
3. `skills` berisi kategori masalah jaringan yang dapat ditangani oleh teknisi.
4. `available_slots` merupakan slot waktu sintetis.
5. Satu teknisi dianggap dapat menangani maksimal satu insiden pada satu slot.
6. Setiap assignment harus memenuhi constraint skill dan ketersediaan.
7. Constraint yang digunakan hanya mencakup aturan yang mempunyai data pendukung pada dataset.
8. Aturan pada dokumen ini bukan merupakan aturan resmi operasional teknisi di Institut Teknologi Del.

---

## 8. Batasan Prototipe

Desain ini belum mempertimbangkan atribut lain seperti:

* tingkat pengalaman teknisi;
* sertifikasi;
* lokasi teknisi;
* beban kerja di luar dataset;
* preferensi teknisi;
* estimasi perjalanan;
* jadwal dinamis secara real-time.

Atribut tersebut tidak digunakan karena belum terdapat data pendukung dalam desain Milestone 2.

Penambahan atribut atau constraint baru perlu didiskusikan dan disepakati terlebih dahulu oleh anggota kelompok agar tetap konsisten dengan formulasi CSP.

---

## 9. Kesimpulan

Desain data teknisi pada Milestone 2 menggunakan tiga atribut utama, yaitu `technician_id`, `skills`, dan `available_slots`.

Ketiga atribut tersebut digunakan untuk mendukung tiga constraint utama, yaitu kesesuaian skill teknisi dengan jenis insiden, ketersediaan teknisi pada slot yang dipilih, dan larangan satu teknisi menangani dua insiden pada slot yang sama.

Desain ini menjadi dasar untuk membangun formulasi CSP, proses AC-3, serta Backtracking dengan MRV dan LCV pada tahap implementasi berikutnya.
