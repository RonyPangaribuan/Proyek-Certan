# Retrieval Evaluation – Proyek Certan

## 1. Tujuan Evaluasi

Evaluasi retrieval dilakukan untuk mengetahui kemampuan sistem pencarian semantik dalam menemukan potongan dokumen yang relevan ketika pengguna mengajukan pertanyaan mengenai penanganan insiden jaringan kampus.

Sistem diharapkan mampu menemukan informasi yang sesuai dengan kebutuhan pengguna, meskipun pertanyaan disampaikan menggunakan susunan kalimat atau istilah yang berbeda dari dokumen sumber.

Evaluasi ini memiliki beberapa tujuan, yaitu:

1. Mengetahui apakah sistem dapat menemukan dokumen dan potongan informasi yang sesuai dengan pertanyaan pengguna.
2. Menguji kemampuan sistem dalam memahami variasi istilah, sinonim, dan parafrasa.
3. Mengetahui kemampuan sistem dalam menangani pertanyaan yang memiliki lebih dari satu kemungkinan sumber relevansi.
4. Menguji respons sistem terhadap pertanyaan yang berada di luar cakupan dokumen.
5. Mengukur kualitas hasil pencarian menggunakan metrik evaluasi retrieval.

Hasil evaluasi nantinya digunakan untuk mengetahui kelebihan dan kekurangan mekanisme pencarian semantik pada Proyek Certan.

## 2. Ruang Lingkup Evaluasi

Evaluasi menggunakan corpus yang telah dijelaskan dalam dokumentasi `knowledge-base.md`.

Berdasarkan dokumentasi Knowledge Base yang disusun oleh Indah, corpus terdiri dari 12 dokumen Markdown simulasi yang membahas berbagai permasalahan jaringan kampus. Proses chunking telah dijalankan menggunakan mode `--dry-run` dan menghasilkan 35 chunk.

Cakupan evaluasi meliputi:

| Aspek | Keterangan |
|---|---|
| Sumber pengujian | 12 dokumen simulasi dalam corpus |
| Jumlah dokumen | 12 dokumen |
| Jumlah chunk | 35 chunk hasil dry-run |
| Format dokumen | Markdown (.md) |
| Jenis pertanyaan | In-domain, sinonim/parafrasa, ambigu, dan out-of-domain |
| Pertanyaan in-domain | 12 pertanyaan |
| Pertanyaan ambigu | 2 pertanyaan |
| Pertanyaan out-of-domain | 3 pertanyaan |
| Metode pencarian | Semantic retrieval berbasis embedding |
| Pembanding relevansi | Dokumen dan chunk yang sesuai dengan pertanyaan |
| Status hasil evaluasi | Belum diuji |

Evaluasi difokuskan pada dokumen yang tersedia dalam corpus, yaitu permasalahan Wi-Fi, DNS, access point, gateway, router, koneksi tidak stabil, eskalasi gangguan, prioritas layanan akademik, SLA penanganan insiden, pelaporan insiden, dan penggantian perangkat.

Perlu diperhatikan bahwa 35 chunk merupakan hasil proses chunking dalam mode `--dry-run`. Jumlah tersebut belum membuktikan bahwa embedding telah dibuat atau data telah disimpan ke ChromaDB.

## 3. Rancangan Mekanisme Retrieval

Mekanisme retrieval yang akan dievaluasi dirancang berdasarkan alur pencarian semantik pada sistem Certan.

Secara umum, alur yang diharapkan adalah sebagai berikut:

1. **Pertanyaan pengguna:** pengguna memasukkan pertanyaan mengenai permasalahan atau penanganan insiden jaringan kampus.
2. **Embedding kueri:** pertanyaan pengguna diubah menjadi representasi vektor menggunakan model embedding.
3. **Pencarian ChromaDB:** representasi vektor pertanyaan digunakan untuk mencari chunk yang memiliki kemiripan semantik dengan pertanyaan tersebut.
4. **Pengambilan top-K chunks:** sistem mengambil sejumlah chunk dengan hasil pencarian terbaik berdasarkan konfigurasi top-K.
5. **Pemeriksaan relevansi:** hasil pencarian dibandingkan dengan ground truth untuk mengetahui apakah informasi yang ditemukan sesuai dengan kebutuhan pertanyaan.
6. **Ambang relevansi:** apabila threshold diterapkan dalam implementasi, hasil pencarian juga diperiksa berdasarkan nilai ambang tersebut.

Rancangan alur:

**Pertanyaan Pengguna → Embedding Kueri → Pencarian ChromaDB → Pengambilan Top-K Chunks → Pemeriksaan Relevansi**

Alur ini merupakan rancangan mekanisme yang akan dievaluasi. Detail model embedding, parameter pencarian, dan penerapan threshold akan disesuaikan dengan implementasi aktual.

## 4. Kumpulan Pertanyaan Benchmark

Pertanyaan benchmark disusun berdasarkan isi 12 dokumen simulasi yang tersedia dalam corpus. Pertanyaan dibuat menggunakan variasi istilah, parafrasa, dan susunan kalimat agar pengujian tidak hanya bergantung pada kesamaan kata secara langsung.

### 4.1 Pertanyaan In-Domain

Pertanyaan in-domain merupakan pertanyaan yang jawabannya diharapkan tersedia dalam dokumen corpus.

| ID | Pertanyaan Uji | Acuan Relevansi | Jenis |
|---|---|---|---|
| Q01 | Apa yang perlu dilakukan ketika koneksi Wi-Fi kampus terasa lambat? | SOP-SIM-01 – Wi-Fi lambat | Parafrasa |
| Q02 | Bagaimana menangani kondisi ketika perangkat tidak dapat terhubung ke jaringan Wi-Fi kampus? | SOP-SIM-02 – Wi-Fi tidak dapat diakses | Langsung |
| Q03 | Apa yang harus diperiksa jika nama domain tidak dapat ditemukan ketika mengakses jaringan? | SOP-SIM-03 – Gangguan DNS | Sinonim |
| Q04 | Bagaimana menangani access point yang tidak menyala atau mengalami gangguan? | SOP-SIM-04 – Kegagalan access point | Parafrasa |
| Q05 | Apa yang perlu diperiksa ketika gateway jaringan tidak dapat dijangkau? | SOP-SIM-05 – Gateway tidak terjangkau | Langsung |
| Q06 | Bagaimana penanganan apabila router mengalami kegagalan dan mengganggu koneksi jaringan? | SOP-SIM-06 – Kegagalan router | Parafrasa |
| Q07 | Apa yang dapat dilakukan ketika koneksi internet sering terputus dan tersambung kembali? | SOP-SIM-07 – Koneksi tidak stabil | Sinonim |
| Q08 | Dalam kondisi seperti apa gangguan jaringan harus dieskalasikan kepada pihak yang bertanggung jawab? | SOP-SIM-08 – Eskalasi gangguan | Langsung |
| Q09 | Bagaimana menentukan prioritas penanganan ketika layanan akademik mengalami gangguan? | SOP-SIM-09 – Prioritas layanan akademik | Parafrasa |
| Q10 | Berapa target waktu respons dan penyelesaian untuk penanganan insiden jaringan? | SOP-SIM-10 – SLA penanganan insiden | Langsung |
| Q11 | Informasi apa saja yang perlu dicantumkan ketika membuat laporan insiden jaringan? | SOP-SIM-11 – Pelaporan insiden | Langsung |
| Q12 | Dalam kondisi apa perangkat jaringan perlu diganti dan bagaimana proses penggantiannya? | SOP-SIM-12 – Penggantian perangkat | Parafrasa |

Seluruh pertanyaan tersebut memiliki acuan dokumen yang sesuai dengan topik dalam corpus. Bagian atau chunk yang benar-benar menjawab setiap pertanyaan akan diverifikasi kembali ketika hasil chunk aktual tersedia.

### 4.2 Pertanyaan Ambigu

Pertanyaan ambigu merupakan pertanyaan yang dapat memiliki lebih dari satu dokumen relevan. Pengujian ini dilakukan untuk mengetahui apakah sistem mampu menemukan beberapa sumber informasi yang berkaitan dengan konteks pertanyaan.

| ID | Pertanyaan Uji | Acuan Relevansi | Alasan Ambigu |
|---|---|---|---|
| A01 | Wi-Fi di suatu ruangan tidak bisa digunakan. Apa yang harus diperiksa terlebih dahulu? | SOP-SIM-02 dan SOP-SIM-04 | Permasalahan dapat berkaitan dengan akses Wi-Fi atau kegagalan access point. |
| A02 | Gangguan jaringan di gedung kampus menyebabkan layanan akademik terganggu. Bagaimana menentukan penanganannya? | SOP-SIM-08 dan SOP-SIM-09 | Pertanyaan berkaitan dengan eskalasi gangguan sekaligus prioritas layanan akademik. |

Pertanyaan ambigu tidak dimasukkan ke dalam jumlah 12 pertanyaan in-domain. Kedua pertanyaan tersebut menjadi pengujian tambahan untuk melihat kemampuan sistem menemukan lebih dari satu sumber yang relevan.

### 4.3 Pertanyaan Out-of-Domain

Pertanyaan out-of-domain merupakan pertanyaan yang topiknya tidak dibahas secara khusus dalam dokumen corpus. Pengujian ini dilakukan untuk mengetahui apakah sistem dapat mengenali keterbatasan sumber informasi yang tersedia.

| ID | Pertanyaan Uji | Acuan Relevansi | Ekspektasi |
|---|---|---|---|
| OOD01 | Bagaimana cara mengatasi konflik alamat IP yang disebabkan oleh DHCP server? | Tidak terdapat dokumen khusus mengenai DHCP | Sistem tidak mengklaim memiliki panduan khusus apabila sumber tidak memadai. |
| OOD02 | Bagaimana cara mengatur VLAN pada perangkat switch jaringan kampus? | Tidak terdapat dokumen khusus mengenai konfigurasi VLAN switch | Sistem tidak menganggap chunk yang hanya mirip secara umum sebagai panduan konfigurasi VLAN. |
| OOD03 | Bagaimana cara mengatur koneksi VPN agar dapat mengakses jaringan kampus dari luar kampus? | Tidak terdapat dokumen khusus mengenai VPN | Sistem mengidentifikasi bahwa pertanyaan berada di luar cakupan sumber yang tersedia. |

Pertanyaan out-of-domain tidak digunakan sebagai pertanyaan yang harus dijawab oleh dokumen corpus. Pertanyaan ini digunakan untuk menguji apakah sistem dapat menghindari pemberian jawaban yang tidak didukung sumber.

## 5. Ground Truth dan Penilaian Relevansi

Ground truth merupakan acuan yang digunakan untuk menentukan apakah hasil pencarian sistem sesuai dengan informasi yang dibutuhkan oleh pengguna.

Dalam evaluasi ini, ground truth disusun berdasarkan dokumen yang tersedia dalam corpus. Setiap pertanyaan memiliki dokumen acuan dan informasi yang diharapkan ditemukan.

Penentuan ground truth dilakukan melalui beberapa tahapan:

1. Membaca dokumen sumber yang berkaitan dengan pertanyaan.
2. Mengidentifikasi bagian dokumen yang mengandung informasi sesuai kebutuhan pertanyaan.
3. Mencocokkan bagian tersebut dengan chunk yang dihasilkan dari proses ingestion.
4. Memberikan label relevansi pada setiap chunk berdasarkan kesesuaiannya dengan pertanyaan.

### 5.1 Kategori Relevansi

| Label | Keterangan | Nilai untuk Metrik |
|---|---|---|
| Relevan | Chunk secara langsung memuat informasi yang dibutuhkan untuk menjawab pertanyaan. | 1 |
| Tidak relevan | Chunk tidak memberikan informasi yang dibutuhkan untuk menjawab pertanyaan. | 0 |
| Sebagian relevan | Chunk memiliki hubungan dengan topik pertanyaan, tetapi informasinya belum cukup untuk menjawab kebutuhan secara lengkap. | Perlu ditinjau sebelum dihitung |

Untuk perhitungan metrik berbasis relevansi biner, kategori sebagian relevan perlu ditinjau terlebih dahulu agar penilaian dilakukan secara konsisten.

### 5.2 Acuan Ground Truth

Acuan dokumen untuk pertanyaan benchmark telah dicantumkan pada tabel di bagian sebelumnya.

Pada tahap rancangan ini, ground truth baru ditetapkan pada tingkat dokumen. ID chunk belum dicantumkan karena perlu menunggu hasil chunk aktual dari implementasi.

Hal ini dilakukan untuk menghindari pembuatan ID chunk yang belum benar-benar dihasilkan oleh sistem.

Ground truth pada tingkat chunk akan dilengkapi setelah hasil ingestion dan metadata aktual tersedia.

## 6. Metrik Evaluasi

Metrik evaluasi digunakan untuk mengukur kualitas hasil retrieval berdasarkan kesesuaian chunk yang ditemukan dengan ground truth.

Evaluasi direncanakan menggunakan Precision@K, Recall@K, dan Mean Reciprocal Rank (MRR).

### 6.1 Precision@K

Precision@K digunakan untuk mengukur proporsi chunk relevan dari seluruh chunk yang dikembalikan sistem pada posisi teratas sebanyak K hasil.

Rumus:

**Precision@K = Jumlah chunk relevan dalam top-K / Jumlah seluruh chunk yang dikembalikan dalam top-K**

Semakin tinggi nilai Precision@K, semakin banyak hasil retrieval yang sesuai dengan pertanyaan pengguna.

Jika sistem mengembalikan hasil kurang dari K, jumlah hasil yang benar-benar dikembalikan digunakan sebagai pembagi.

### 6.2 Recall@K

Recall@K digunakan untuk mengukur seberapa banyak chunk relevan yang berhasil ditemukan oleh sistem dibandingkan dengan seluruh chunk relevan yang telah ditetapkan dalam ground truth.

Rumus:

**Recall@K = Jumlah chunk relevan yang ditemukan dalam top-K / Total chunk relevan dalam ground truth**

Semakin tinggi nilai Recall@K, semakin banyak informasi relevan yang berhasil ditemukan oleh sistem.

### 6.3 Mean Reciprocal Rank (MRR)

MRR digunakan untuk mengukur posisi hasil relevan pertama yang ditemukan oleh sistem.

Rumus:

**MRR = (1/N) × Σ (1/rank_i)**

Keterangan:

- N adalah jumlah pertanyaan yang dievaluasi.
- rank_i adalah posisi hasil relevan pertama untuk pertanyaan ke-i.
- Jika tidak ditemukan hasil relevan, nilai reciprocal rank untuk pertanyaan tersebut adalah 0.

Semakin tinggi nilai MRR, semakin baik posisi hasil relevan pertama yang ditampilkan sistem.

### 6.4 Cosine Similarity

Cosine similarity digunakan untuk menjelaskan tingkat kemiripan arah antara vektor embedding pertanyaan dan vektor embedding chunk.

Nilai kemiripan dapat menjadi informasi pendukung dalam analisis hasil retrieval. Namun, nilai similarity atau distance yang ditampilkan harus mengikuti konfigurasi aktual dari implementasi ChromaDB.

Nilai tersebut tidak boleh langsung dianggap sebagai label relevansi. Relevansi tetap ditentukan berdasarkan pemeriksaan isi chunk terhadap kebutuhan pertanyaan.

Nilai K yang digunakan dalam perhitungan akan mengikuti konfigurasi top-K pada implementasi sistem.

## 7. Prosedur Pengujian

Pengujian retrieval direncanakan melalui tahapan berikut:

1. Memastikan seluruh dokumen corpus telah diproses melalui ingestion.
2. Memastikan embedding telah dibuat menggunakan model yang digunakan dalam implementasi.
3. Memastikan data embedding dan metadata telah disimpan ke ChromaDB.
4. Memasukkan pertanyaan benchmark satu per satu ke sistem retrieval.
5. Mencatat hasil top-K chunks yang dikembalikan sistem.
6. Mencocokkan setiap hasil retrieval dengan ground truth.
7. Memberikan label relevansi pada setiap hasil pencarian.
8. Menghitung Precision@K, Recall@K, dan MRR berdasarkan hasil yang telah diberi label.
9. Menganalisis hasil pencarian yang sesuai maupun yang tidak sesuai.
10. Melakukan pengujian tambahan menggunakan pertanyaan ambigu dan out-of-domain.

Tahapan tersebut merupakan prosedur yang direncanakan. Hasil pelaksanaan akan dicatat setelah implementasi retrieval tersedia dan pengujian benar-benar dijalankan.

## 8. Rancangan Tabel Pelaporan Hasil

Hasil pengujian akan dicatat berdasarkan pertanyaan benchmark, dokumen acuan, hasil retrieval, dan label relevansi.

Pada tahap penyusunan rancangan ini, hasil retrieval belum tersedia sehingga tabel disiapkan terlebih dahulu untuk diisi setelah pengujian dilakukan.

### 8.1 Tabel Hasil Pertanyaan In-Domain

| ID | Dokumen Acuan | Hasil Top-K Retrieval | Hit/Miss | Catatan |
|---|---|---|---|---|
| Q01 | SOP-SIM-01 | Belum diuji | - | Menunggu hasil retrieval |
| Q02 | SOP-SIM-02 | Belum diuji | - | Menunggu hasil retrieval |
| Q03 | SOP-SIM-03 | Belum diuji | - | Menunggu hasil retrieval |
| Q04 | SOP-SIM-04 | Belum diuji | - | Menunggu hasil retrieval |
| Q05 | SOP-SIM-05 | Belum diuji | - | Menunggu hasil retrieval |
| Q06 | SOP-SIM-06 | Belum diuji | - | Menunggu hasil retrieval |
| Q07 | SOP-SIM-07 | Belum diuji | - | Menunggu hasil retrieval |
| Q08 | SOP-SIM-08 | Belum diuji | - | Menunggu hasil retrieval |
| Q09 | SOP-SIM-09 | Belum diuji | - | Menunggu hasil retrieval |
| Q10 | SOP-SIM-10 | Belum diuji | - | Menunggu hasil retrieval |
| Q11 | SOP-SIM-11 | Belum diuji | - | Menunggu hasil retrieval |
| Q12 | SOP-SIM-12 | Belum diuji | - | Menunggu hasil retrieval |

### 8.2 Tabel Hasil Pertanyaan Ambigu

| ID | Dokumen Acuan | Hasil Top-K Retrieval | Hit/Miss | Catatan |
|---|---|---|---|---|
| A01 | SOP-SIM-02 dan SOP-SIM-04 | Belum diuji | - | Menunggu hasil retrieval |
| A02 | SOP-SIM-08 dan SOP-SIM-09 | Belum diuji | - | Menunggu hasil retrieval |

### 8.3 Tabel Hasil Pertanyaan Out-of-Domain

| ID | Topik Pertanyaan | Hasil Top-K Retrieval | Ekspektasi | Status |
|---|---|---|---|---|
| OOD01 | DHCP dan konflik IP | Belum diuji | Tidak mengklaim memiliki sumber khusus yang memadai | Belum diuji |
| OOD02 | Konfigurasi VLAN switch | Belum diuji | Tidak mengklaim memiliki panduan khusus VLAN | Belum diuji |
| OOD03 | Konfigurasi VPN | Belum diuji | Mengidentifikasi keterbatasan cakupan corpus | Belum diuji |

Untuk pertanyaan out-of-domain, sistem tidak harus selalu menghasilkan daftar kosong karena pencarian semantik dapat mengembalikan chunk yang memiliki kemiripan. Hal yang perlu dinilai adalah apakah sistem mampu menghindari klaim bahwa chunk yang tidak sesuai merupakan sumber jawaban yang memadai.

### 8.4 Rekapitulasi Metrik

| Metrik | Hasil |
|---|---|
| Precision@K | Belum dihitung |
| Recall@K | Belum dihitung |
| MRR | Belum dihitung |
| Jumlah pertanyaan benchmark | 17 pertanyaan |
| Pertanyaan in-domain | 12 pertanyaan |
| Pertanyaan ambigu | 2 pertanyaan |
| Pertanyaan out-of-domain | 3 pertanyaan |

Metrik utama dihitung berdasarkan pertanyaan dan label relevansi yang telah ditetapkan. Hasil pertanyaan ambigu dan out-of-domain juga dianalisis secara terpisah agar karakteristik pengujiannya tidak tercampur dengan pengujian in-domain.

## 9. Keterbatasan Evaluasi

Evaluasi ini memiliki beberapa keterbatasan yang perlu diperhatikan.

1. **Keterbatasan jumlah corpus:** corpus yang digunakan hanya terdiri dari 12 dokumen simulasi sehingga belum mencakup seluruh permasalahan jaringan yang mungkin terjadi di lingkungan kampus.
2. **Dokumen bersifat simulasi:** dokumen yang digunakan merupakan dokumen yang disusun untuk kebutuhan proyek dan bukan SOP resmi IT Del. Oleh karena itu, hasil evaluasi tidak dapat langsung dianggap menggambarkan kualitas penanganan insiden jaringan secara nyata.
3. **Jumlah pertanyaan pengujian:** benchmark terdiri dari 12 pertanyaan in-domain, 2 pertanyaan ambigu, dan 3 pertanyaan out-of-domain. Jumlah tersebut masih terbatas untuk menggambarkan seluruh variasi pertanyaan pengguna.
4. **Ketergantungan pada kualitas dokumen:** kualitas retrieval dipengaruhi oleh kejelasan isi dokumen, struktur heading, proses pembersihan teks, dan pembagian chunk.
5. **Ketergantungan pada model embedding:** kemampuan sistem menemukan informasi juga dipengaruhi oleh model embedding yang digunakan dan kesesuaiannya dengan bahasa pertanyaan.
6. **Penilaian relevansi bersifat subjektif:** penentuan relevansi chunk dapat berbeda antarpenilai, terutama pada pertanyaan ambigu atau chunk yang hanya memuat sebagian informasi.
7. **Keterbatasan domain:** pengujian hanya berfokus pada permasalahan jaringan kampus yang dibahas dalam corpus. Hasilnya belum dapat digunakan untuk menyimpulkan kemampuan sistem pada domain lain.
8. **Keterbatasan pengujian out-of-domain:** keberadaan pertanyaan out-of-domain belum membuktikan bahwa sistem memiliki fitur untuk menolak pertanyaan di luar cakupan. Perilaku tersebut tetap perlu diperiksa melalui pengujian implementasi.

## 10. Kesimpulan

Dokumentasi ini menyusun rancangan evaluasi semantic retrieval pada Proyek Certan berdasarkan 12 dokumen simulasi yang tersedia dalam corpus.

Pengujian dirancang menggunakan 12 pertanyaan in-domain, 2 pertanyaan ambigu, dan 3 pertanyaan out-of-domain. Evaluasi akan menggunakan Precision@K, Recall@K, dan MRR untuk mengukur kesesuaian serta posisi hasil retrieval berdasarkan ground truth.

Pada tahap penyusunan dokumentasi, proses chunking telah menghasilkan 35 chunk melalui mode `--dry-run`. Hasil pengujian retrieval dan perhitungan metrik belum dimasukkan karena bagian tersebut memerlukan bukti implementasi dan eksekusi sistem.

Dokumentasi ini akan diperbarui setelah hasil implementasi tersedia sehingga penilaian kualitas retrieval dapat didasarkan pada hasil pengujian yang sebenarnya.