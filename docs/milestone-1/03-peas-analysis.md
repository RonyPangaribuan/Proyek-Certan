# PEAS Analysis

## A. PEAS Purpose

PEAS digunakan untuk menjelaskan bagaimana sistem pendukung keputusan bekerja dalam menentukan prioritas penanganan insiden jaringan kampus. Analisis ini mencakup tujuan sistem, lingkungan tempat sistem bekerja, informasi yang diterima sistem, serta keluaran yang dihasilkan.

Pada proyek ini, PEAS difokuskan pada proses prioritisasi insiden. Sistem tidak melakukan perbaikan jaringan secara langsung, tetapi memberikan rekomendasi urutan insiden yang perlu ditangani berdasarkan karakteristik masing-masing insiden.

## B. Agent

Agent pada sistem ini adalah sistem pendukung keputusan berbasis AI yang menerima informasi dari beberapa laporan insiden jaringan kampus. Sistem menganalisis karakteristik dari setiap insiden untuk menentukan prioritas penanganannya.

Sistem memberikan rekomendasi urutan insiden yang perlu ditangani terlebih dahulu. Sistem tidak melakukan perbaikan jaringan secara langsung dan keputusan akhir tetap berada pada pihak yang bertanggung jawab terhadap penanganan jaringan.

## C. Performance Measure

Kinerja sistem diukur berdasarkan kemampuan sistem dalam memberikan rekomendasi prioritas yang sesuai dengan karakteristik insiden. Beberapa hal yang diperhatikan adalah:

- Insiden dengan dampak tinggi tidak terlambat mendapatkan perhatian.
- Insiden dengan tingkat urgensi tinggi mendapatkan prioritas yang sesuai.
- Tingkat kritisitas layanan dipertimbangkan dalam menentukan prioritas.
- Jumlah pengguna yang terdampak ikut dipertimbangkan.
- Waktu tunggu insiden diperhatikan dalam proses prioritisasi.
- Sistem memberikan hasil yang konsisten ketika diberikan kondisi input yang sama.
- Urutan prioritas yang dihasilkan dapat dijelaskan berdasarkan karakteristik insiden.

## D. Environment

Environment pada sistem terdiri dari kumpulan laporan insiden jaringan kampus yang akan diproses untuk menentukan urutan penanganannya. Setiap laporan memiliki karakteristik yang dapat digunakan oleh sistem dalam melakukan prioritisasi.

Informasi yang terdapat dalam environment meliputi:

- Jenis atau kategori insiden.
- Lokasi atau layanan yang terdampak.
- Tingkat urgensi insiden.
- Tingkat dampak insiden.
- Jumlah pengguna yang terdampak.
- Tingkat kritisitas layanan.
- Waktu tunggu sejak insiden dilaporkan.
- Perkiraan waktu penanganan insiden.

Pada Milestone 1, sistem bekerja menggunakan kumpulan data insiden sebagai sebuah snapshot. Artinya, sistem memproses data yang tersedia pada saat proses dilakukan dan belum menangani perubahan insiden secara real-time.

## E. Actuators

Actuators merupakan keluaran atau tindakan yang dapat dilakukan oleh sistem berdasarkan hasil analisis terhadap insiden. Pada proyek ini, actuators berfokus pada pemberian rekomendasi kepada pihak yang menangani jaringan.

Output yang dihasilkan sistem meliputi:

- Tingkat prioritas setiap insiden.
- Rekomendasi urutan insiden yang perlu ditangani.
- Informasi mengenai faktor-faktor yang memengaruhi prioritas suatu insiden.

Sistem tidak melakukan tindakan fisik atau perbaikan jaringan secara otomatis, seperti memperbaiki router, mengubah konfigurasi jaringan, atau melakukan troubleshooting secara langsung.

## F. Sensors

Sensors merupakan informasi atau data yang diterima oleh sistem sebagai dasar untuk melakukan analisis dan menentukan prioritas insiden. Pada proyek ini, sensors berasal dari data laporan insiden jaringan.

Informasi yang digunakan meliputi:

| Sensor | Penjelasan |
|---|---|
| `category` | Menunjukkan jenis atau kategori insiden jaringan yang terjadi. |
| `location` | Menunjukkan lokasi atau layanan yang terdampak oleh insiden. |
| `urgency` | Menunjukkan seberapa mendesak suatu insiden untuk ditangani. |
| `impact` | Menunjukkan seberapa besar dampak insiden terhadap layanan atau kegiatan kampus. |
| `affected_users` | Menunjukkan jumlah pengguna yang terdampak oleh insiden. |
| `service_criticality` | Menunjukkan tingkat kepentingan atau kritisitas layanan yang terdampak. |
| `waiting_time_min` | Menunjukkan berapa lama insiden telah menunggu sejak dilaporkan. |
| `estimated_handling_time_min` | Menunjukkan perkiraan waktu yang dibutuhkan untuk menangani insiden. |

## G. PEAS Table

| Komponen | Deskripsi |
|---|---|
| **Performance Measure** | Prioritas sesuai tingkat urgensi, dampak, kritisitas layanan, jumlah pengguna terdampak, dan waktu tunggu. Hasil harus konsisten dan dapat dijelaskan. |
| **Environment** | Kumpulan laporan insiden jaringan kampus yang berisi karakteristik setiap insiden. Pada Milestone 1, data diproses sebagai snapshot dan belum secara real-time. |
| **Actuators** | Menghasilkan tingkat prioritas, rekomendasi urutan penanganan, dan informasi faktor yang memengaruhi prioritas. |
| **Sensors** | `category`, `location`, `urgency`, `impact`, `affected_users`, `service_criticality`, `waiting_time_min`, dan `estimated_handling_time_min`. |

## H. Environment Classification

Environment pada sistem dapat diklasifikasikan berdasarkan beberapa karakteristik berikut:

| Dimensi | Klasifikasi | Penjelasan |
|---|---|---|
| **Observable** | Fully Observable | Sistem menggunakan informasi yang tersedia pada laporan insiden sebagai dasar untuk menentukan prioritas. Pada Milestone 1, data yang dibutuhkan dianggap tersedia. |
| **Deterministic / Stochastic** | Deterministic | Dengan input dan kondisi yang sama, sistem diharapkan menghasilkan hasil yang konsisten. |
| **Episodic / Sequential** | Sequential | Urutan penanganan satu insiden dapat memengaruhi kondisi dan biaya dari urutan penanganan berikutnya. |
| **Static / Dynamic** | Static pada Milestone 1 | Data diproses sebagai snapshot sehingga kondisi tidak berubah selama proses pencarian. Dalam lingkungan nyata, kondisi jaringan dapat berubah. |
| **Discrete / Continuous** | Discrete | Insiden dan tindakan penanganannya direpresentasikan sebagai kondisi dan langkah-langkah yang terpisah. |
| **Single-Agent / Multi-Agent** | Single-Agent pada Milestone 1 | Sistem pencarian dipandang sebagai satu agent yang menentukan urutan prioritas. Pihak seperti teknisi dan administrator diposisikan sebagai pengguna atau stakeholder, bukan agent dalam proses pencarian. |

### Catatan

Klasifikasi di atas disesuaikan dengan kondisi Milestone 1. Prototype menggunakan data insiden yang sudah tersedia sehingga environment diperlakukan lebih sederhana. Pada kondisi nyata, lingkungan jaringan dapat bersifat lebih dinamis dan melibatkan lebih banyak pihak.

## I. Linkage to Project

Analisis PEAS digunakan sebagai dasar untuk menjelaskan bagaimana sistem pendukung keputusan melakukan prioritisasi insiden jaringan kampus.

Informasi yang diterima melalui sensors digunakan untuk menganalisis karakteristik setiap insiden. Hasil analisis tersebut kemudian digunakan untuk menghasilkan rekomendasi prioritas dan urutan penanganan melalui actuators.

PEAS juga membantu memperjelas batasan sistem pada Milestone 1. Sistem hanya memberikan rekomendasi untuk membantu pihak yang bertanggung jawab dalam menentukan insiden yang perlu ditangani terlebih dahulu. Sistem tidak melakukan troubleshooting, perbaikan jaringan, atau perubahan konfigurasi jaringan secara otomatis.

Dengan demikian, PEAS mendukung tujuan utama proyek, yaitu membantu proses pengambilan keputusan dalam menentukan prioritas penanganan beberapa insiden jaringan kampus.