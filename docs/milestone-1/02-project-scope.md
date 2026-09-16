# Project Scope

## 1. Scope Proyek

Proyek berfokus pada pengembangan sistem pendukung keputusan berbasis AI untuk membantu menentukan prioritas penanganan laporan insiden jaringan di lingkungan kampus.

Pada Milestone 1, fokus utama proyek adalah membangun fondasi masalah, merepresentasikan insiden sebagai masalah pencarian, dan merancang mekanisme awal untuk menentukan urutan penanganan insiden.

## 2. In Scope

Fitur dan aktivitas yang termasuk dalam ruang lingkup awal proyek adalah:

### 2.1 Representasi Laporan Insiden

Sistem menggunakan data laporan insiden jaringan yang memiliki atribut tertentu, seperti:

- ID insiden;
- jenis gangguan;
- lokasi atau layanan terdampak;
- tingkat urgensi;
- tingkat dampak;
- jumlah pengguna terdampak;
- waktu laporan;
- tingkat kekritisan layanan.

### 2.2 Prioritisasi Insiden

Sistem menentukan laporan yang sebaiknya ditangani terlebih dahulu berdasarkan karakteristik masing-masing insiden.

Prioritisasi tidak hanya mempertimbangkan urutan laporan masuk, tetapi juga mempertimbangkan tingkat kepentingan insiden.

### 2.3 Formulasi Masalah Pencarian

Masalah prioritisasi akan direpresentasikan sebagai search problem yang memiliki:

- initial state;
- state;
- action;
- transition model;
- goal state;
- path cost.

Algoritma seperti **Uniform Cost Search (UCS)** dan/atau **A\*** akan dianalisis untuk menentukan pendekatan yang sesuai.

### 2.4 Data Awal

Pada tahap prototype, proyek dapat menggunakan **data sintetis** yang dirancang untuk merepresentasikan kondisi laporan insiden jaringan kampus.

Data sintetis digunakan agar algoritma dan rancangan sistem dapat dikembangkan serta diuji sebelum tersedia data operasional sebenarnya.

## 3. Out of Scope untuk Milestone 1

Beberapa fitur berikut belum menjadi fokus utama Milestone 1:

- troubleshooting jaringan secara otomatis;
- eksekusi perbaikan jaringan secara langsung;
- integrasi dengan perangkat jaringan kampus;
- monitoring jaringan secara real-time;
- prediksi gangguan jaringan;
- integrasi dengan sistem helpdesk kampus yang sebenarnya;
- implementasi penuh penugasan teknisi;
- penggunaan knowledge base dan Retrieval-Augmented Generation;
- implementasi AI agent lengkap.

Fitur-fitur tersebut dapat dikembangkan pada milestone berikutnya apabila sesuai dengan kebutuhan proyek.

## 4. Batasan Sistem

Untuk menjaga proyek tetap realistis dan dapat dikembangkan secara bertahap, digunakan beberapa batasan berikut:

1. Sistem hanya berfokus pada **insiden yang berkaitan dengan jaringan kampus**.
2. Sistem tidak melakukan perbaikan jaringan secara otomatis.
3. Output sistem berupa **rekomendasi keputusan**, bukan keputusan final yang wajib dilaksanakan.
4. Data awal dapat berupa data sintetis.
5. Jumlah dan jenis atribut insiden akan dibatasi pada atribut yang relevan terhadap proses prioritisasi.
6. Kondisi jaringan fisik secara real-time belum menjadi input sistem pada tahap awal.

## 5. Input Sistem

Contoh input yang dapat digunakan:

```text
Incident ID       : INC001
Jenis Gangguan    : Network Down
Lokasi            : Laboratorium
Urgensi           : 5
Dampak             : 4
Pengguna Terdampak: 40
Service Criticality: 4
Waiting Time      : 20 menit
```

## 6. Output Sistem

Output utama yang diharapkan berupa rekomendasi tingkat atau urutan prioritas.

Contoh:

```text
1. INC004 → Prioritas Tinggi
2. INC001 → Prioritas Tinggi
3. INC003 → Prioritas Sedang
4. INC002 → Prioritas Rendah
```

Output dapat disertai informasi yang menjelaskan faktor utama yang memengaruhi prioritas.

## 7. Kriteria Keberhasilan Awal

Milestone 1 dianggap berhasil apabila:

1. masalah bisnis dan masalah AI telah didefinisikan dengan jelas;
2. ruang lingkup dan batasan proyek telah ditentukan;
3. PEAS dapat dirumuskan secara konsisten;
4. masalah dapat direpresentasikan sebagai search problem;
5. dataset awal dapat merepresentasikan beberapa jenis insiden jaringan;
6. algoritma pencarian yang digunakan memiliki definisi state, action, goal, dan cost yang jelas;
7. sistem mampu menghasilkan rekomendasi urutan penanganan dari beberapa insiden contoh.

## 8. Arah Pengembangan Milestone Berikutnya

Scope proyek dapat diperluas secara bertahap dengan tetap mempertahankan masalah utama penanganan insiden jaringan.

Contoh arah pengembangan:

```text
Milestone 1
Prioritisasi insiden
        ↓
Milestone 2
Optimasi keputusan dan penugasan berdasarkan constraint
        ↓
Milestone 3
Knowledge base untuk informasi penanganan/troubleshooting
        ↓
Milestone 4
AI agent yang mengintegrasikan berbagai komponen
        ↓
Milestone 5
Prototype sistem terintegrasi
```

Dengan pendekatan tersebut, setiap milestone menambahkan kemampuan baru tanpa mengubah masalah utama proyek.