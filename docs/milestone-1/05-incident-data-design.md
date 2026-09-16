05-incident-data-design.md
Tujuannya apa?

Sederhananya:

Kita mau menentukan bentuk data insiden yang nantinya diberikan kepada algoritma.

Bayangkan nanti ada laporan:

INC001
WiFi lambat
Ruang Kelas
Urgency 2
Impact 2
15 pengguna
Criticality 2
Menunggu 35 menit
Estimasi penanganan 20 menit

Algoritma membutuhkan data seperti ini supaya bisa membandingkan:

INC001
INC002
INC003
INC004
...

lalu mencari urutan penanganannya.

4. Isi file 05 harus bagaimana?

Kita buat struktur seperti ini:

# Incident Data Design

## 1. Tujuan Data

## 2. Sumber dan Karakteristik Data

## 3. Data Dictionary

## 4. Definisi Atribut

## 5. Contoh Data Sintetis

## 6. Asumsi Data

## 7. Validasi Data

## 8. Keterkaitan Data dengan Prioritisasi

## 9. Kesimpulan
5. Bagian 1 — Tujuan Data

Di sini kamu menjawab:

"Kenapa kita membuat data ini?"

Jawabannya:

Data digunakan untuk merepresentasikan laporan insiden jaringan sehingga sistem dapat membandingkan karakteristik beberapa insiden dan menentukan prioritas penanganannya.

Kemudian jelaskan:

Data pada Milestone 1 adalah data sintetis, bukan data jaringan IT Del yang sebenarnya.

Ini sesuai dengan scope yang sudah mengatakan prototype boleh menggunakan data sintetis.

6. Bagian 2 — Sumber dan Karakteristik Data

Di sini kamu menjelaskan:

Sumber:
Data sintetis yang dibuat oleh tim.

Bukan:
Data operasional asli IT Del.

Tujuan:
Prototype + pengujian algoritma.

Kenapa sintetis?

Karena kita belum menggunakan data operasional sebenarnya.

7. Bagian 3 — Data Dictionary

Nah, ini salah satu bagian utama.

Kita gunakan 9 atribut:

incident_id
category
location
urgency
impact
affected_users
service_criticality
waiting_time_min
estimated_handling_time_min

Buat tabel:

Field	Type	Range/Format	Contoh	Keterangan
incident_id	String	INCxxx	INC001	ID unik insiden
category	String	kategori gangguan	wifi_slow	Jenis gangguan
location	String	lokasi/layanan	Laboratorium	Lokasi terdampak
urgency	Integer	1–5	4	Tingkat urgensi
impact	Integer	1–5	4	Besarnya dampak
affected_users	Integer	≥ 0	40	Jumlah pengguna terdampak
service_criticality	Integer	1–5	4	Tingkat kekritisan layanan
waiting_time_min	Integer	≥ 0	15	Lama menunggu
estimated_handling_time_min	Integer	> 0	30	Estimasi waktu penanganan

Atribut ini tidak kita karang sembarangan. 01-problem-framing.md memang sudah menyebut jenis gangguan, lokasi/layanan, urgency, impact, affected users, waktu laporan, dan service criticality. 02-project-scope.md juga sudah menetapkan input seperti waiting time dan estimated handling time.

8. Bagian 4 — Definisi atribut

Setelah tabel, kamu jelaskan satu-satu.

Contohnya:

urgency

Menunjukkan seberapa mendesak sebuah insiden perlu ditangani.

Nilai	Makna
1	Sangat rendah
2	Rendah
3	Sedang
4	Tinggi
5	Sangat mendesak/kritis

Lakukan hal yang sama untuk:

impact
service_criticality

Sedangkan:

affected_users → jumlah pengguna yang terdampak.

waiting_time_min → berapa menit insiden sudah menunggu.

estimated_handling_time_min → perkiraan berapa menit insiden membutuhkan penanganan.

9. Bagian 5 — Data sintetis

Ini yang paling menarik.

Kita buat 12 insiden.

Misalnya:

ID	Category	Location	Urgency	Impact	Users	Criticality	Waiting	Handling
INC001	wifi_slow	Ruang Kelas	2	2	15	2	35	20
INC002	network_down	Laboratorium	4	4	40	4	15	30
INC003	network_down	Layanan Akademik	5	5	120	5	10	40
INC004	unstable_connection	Perpustakaan	3	3	25	3	180	25
INC005	access_point_failure	Asrama	4	3	60	3	45	35
INC006	dns_issue	Ruang Administrasi	3	2	30	4	70	20
INC007	wifi_down	Gedung Perkuliahan	4	5	80	4	25	45
INC008	router_failure	Laboratorium	5	4	20	4	5	35
INC009	gateway_unreachable	Layanan Akademik	5	5	55	5	20	50
INC010	wifi_slow	Perpustakaan	2	2	50	2	150	25
INC011	unstable_connection	Ruang Kelas	3	4	10	2	90	15
INC012	wifi_down	Asrama	4	3	100	3	60	40

Perhatikan:

Tidak semuanya tinggi.

Ada yang:

kritis dan banyak pengguna;
urgency tinggi tapi pengguna sedikit;
urgency sedang tapi sudah lama menunggu;
impact tinggi tapi waiting pendek;
pengguna banyak tapi criticality sedang.

Ini sengaja supaya nanti algoritma mempunyai kasus yang bisa dibandingkan.

10. Bagian 6 — Asumsi

Tulis sederhana:

- Data merupakan data sintetis.
- Urgency menggunakan skala 1–5.
- Impact menggunakan skala 1–5.
- Service criticality menggunakan skala 1–5.
- Affected users merupakan estimasi.
- Waiting time dihitung dalam menit.
- Estimated handling time merupakan estimasi.
- Data belum berasal dari monitoring jaringan real-time.

Ini juga konsisten dengan batasan scope bahwa kondisi jaringan fisik real-time belum menjadi input sistem.

11. Bagian 7 — Validasi

Kita tentukan aturan:

incident_id harus unik
urgency = 1–5
impact = 1–5
service_criticality = 1–5
affected_users >= 0
waiting_time_min >= 0
estimated_handling_time_min > 0
category tidak boleh kosong
location tidak boleh kosong

Jadi kalau ada:

urgency = 7

❌ Tidak valid.

12. Bagian 8 — Hubungan dengan prioritas

Ini penting.

Kamu jelaskan bahwa data tersebut nantinya menjadi dasar untuk menentukan prioritas.

Contohnya:

Insiden dengan tingkat urgency, impact, jumlah pengguna terdampak, dan service criticality yang tinggi dapat memiliki konsekuensi lebih besar apabila penanganannya ditunda. Waiting time juga dapat digunakan untuk mempertimbangkan insiden yang telah menunggu lebih lama.

Perhatikan: jangan bilang:

urgency = 30%, impact = 25%...

Belum.

Karena bobot final belum ditentukan.
