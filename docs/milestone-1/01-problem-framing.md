# Problem Framing

## 1. Judul Proyek

**Sistem Pendukung Keputusan Berbasis AI untuk Prioritisasi dan Penanganan Insiden Jaringan Kampus**

## 2. Latar Belakang

Jaringan komputer merupakan salah satu infrastruktur penting dalam mendukung kegiatan akademik dan operasional di lingkungan kampus. Berbagai aktivitas seperti perkuliahan, penggunaan laboratorium, akses sistem informasi akademik, layanan administrasi, dan aktivitas mahasiswa bergantung pada ketersediaan jaringan yang baik.

Dalam operasionalnya, gangguan jaringan dapat terjadi pada waktu yang sama atau berdekatan. Gangguan tersebut dapat memiliki tingkat dampak dan urgensi yang berbeda. Sebagai contoh, gangguan jaringan pada layanan yang digunakan oleh banyak pengguna dapat membutuhkan penanganan lebih cepat dibandingkan gangguan yang hanya berdampak pada sebagian kecil pengguna.

Jika laporan gangguan hanya ditangani berdasarkan urutan laporan masuk, tanpa mempertimbangkan tingkat dampak dan urgensi, maka insiden yang lebih kritis berpotensi terlambat ditangani.

Oleh karena itu, diperlukan sebuah sistem pendukung keputusan yang dapat membantu menentukan laporan insiden jaringan yang perlu ditangani terlebih dahulu berdasarkan karakteristik setiap insiden.

## 3. Identifikasi Masalah

Permasalahan utama dalam proyek ini adalah adanya beberapa laporan insiden jaringan yang dapat masuk dalam waktu yang berdekatan, sementara setiap insiden memiliki tingkat kepentingan yang berbeda.

Beberapa faktor yang dapat membedakan tingkat kepentingan suatu insiden antara lain:

- tingkat urgensi;
- tingkat dampak;
- jumlah pengguna yang terdampak;
- tingkat kekritisan layanan;
- lama waktu laporan menunggu;
- jenis gangguan jaringan.

Tanpa mekanisme prioritisasi yang terstruktur, proses penentuan laporan yang harus ditangani terlebih dahulu dapat bergantung pada penilaian manual dan berpotensi menghasilkan keputusan yang kurang konsisten.

## 4. Problem Statement

Bagaimana membangun sistem pendukung keputusan berbasis AI yang dapat menentukan prioritas penanganan dari beberapa laporan insiden jaringan kampus berdasarkan karakteristik dan tingkat kepentingan setiap insiden?

## 5. Tujuan Proyek

Proyek ini bertujuan untuk mengembangkan sistem pendukung keputusan yang dapat:

1. Merepresentasikan laporan insiden jaringan dalam bentuk data yang dapat diproses oleh sistem.
2. Menganalisis karakteristik setiap laporan insiden.
3. Menentukan tingkat atau urutan prioritas penanganan insiden.
4. Memberikan rekomendasi kepada pihak yang bertanggung jawab dalam menentukan insiden yang perlu ditangani terlebih dahulu.
5. Menjadi fondasi untuk pengembangan mekanisme penanganan insiden yang lebih lengkap pada milestone berikutnya.

## 6. Gambaran Solusi

Sistem menerima beberapa laporan insiden jaringan sebagai input. Setiap laporan memiliki sejumlah atribut yang menggambarkan kondisi insiden.

Contoh atribut yang dapat digunakan meliputi:

- jenis gangguan;
- lokasi atau layanan yang terdampak;
- tingkat urgensi;
- tingkat dampak;
- jumlah pengguna yang terdampak;
- waktu laporan diterima;
- tingkat kekritisan layanan.

Data tersebut kemudian diproses menggunakan pendekatan kecerdasan buatan dan algoritma pencarian untuk menghasilkan rekomendasi urutan penanganan.

Secara umum, alur sistem adalah:

```text
Laporan Insiden
       ↓
Representasi Karakteristik Insiden
       ↓
Proses Analisis dan Pencarian
       ↓
Rekomendasi Prioritas Penanganan
```

## 7. Contoh Kasus

Misalkan terdapat tiga laporan insiden jaringan:

| ID | Insiden | Dampak | Urgensi | Pengguna Terdampak |
|---|---|---:|---:|---:|
| INC001 | Wi-Fi pada satu ruangan lambat | 2 | 2 | 10 |
| INC002 | Internet laboratorium terputus | 4 | 4 | 40 |
| INC003 | Layanan jaringan akademik tidak dapat diakses | 5 | 5 | 100 |

Sistem diharapkan dapat menganalisis kondisi tersebut dan menghasilkan rekomendasi prioritas, misalnya:

1. INC003
2. INC002
3. INC001

Urutan tersebut tidak hanya berdasarkan waktu laporan masuk, tetapi berdasarkan karakteristik dan tingkat kepentingan setiap insiden.

## 8. Stakeholder

Stakeholder yang berkaitan dengan sistem antara lain:

- pengelola atau administrator jaringan kampus;
- teknisi atau petugas yang menangani gangguan jaringan;
- pengguna jaringan kampus sebagai pelapor insiden;
- pihak pengelola layanan TI kampus.

## 9. Nilai yang Diharapkan

Sistem diharapkan dapat membantu proses penanganan insiden menjadi lebih:

- terstruktur;
- konsisten;
- transparan;
- responsif terhadap insiden dengan tingkat dampak tinggi.

Sistem berfungsi sebagai **pendukung keputusan**, sehingga keputusan akhir tetap dapat dilakukan oleh pihak yang bertanggung jawab terhadap operasional jaringan.