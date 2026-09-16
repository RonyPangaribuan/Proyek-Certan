# Search Problem Formulation

## A. Overview

Masalah prioritisasi insiden jaringan kampus dapat direpresentasikan sebagai sebuah search problem. Sistem perlu menentukan urutan penanganan dari beberapa insiden berdasarkan karakteristik masing-masing insiden.

Masalah ini tidak hanya berupa pengurutan sederhana karena terdapat beberapa kemungkinan urutan penanganan. Setiap urutan dapat menghasilkan kondisi dan cost yang berbeda. Oleh karena itu, proses penentuan urutan dapat dipandang sebagai proses pencarian pada state space.

Pada Milestone 1, formulasi search problem digunakan untuk menjelaskan struktur masalah sebelum dilakukan implementasi algoritma pencarian. Algoritma yang akan dianalisis adalah Uniform Cost Search (UCS) dan A*.

## B. State

State menggambarkan kondisi proses prioritisasi pada suatu tahap pencarian.

Satu state terdiri dari:

- daftar insiden yang belum dipilih untuk ditangani;
- daftar insiden yang sudah dipilih;
- urutan penanganan yang sudah terbentuk;
- accumulated path cost dari urutan yang telah dipilih.

Contohnya, jika terdapat tiga insiden yaitu INC001, INC002, dan INC003, maka kondisi awal dapat direpresentasikan sebagai:

```text
Unhandled = {INC001, INC002, INC003}
Handled = {}
Sequence = []
Cost = 0

Setelah satu insiden dipilih, kondisi state akan berubah sesuai dengan action yang dilakukan.

## C. Initial State

Initial state merupakan kondisi ketika proses pencarian dimulai.

Pada initial state:

seluruh insiden belum dipilih;
belum terdapat urutan penanganan;
accumulated cost bernilai 0.

Contoh:

Unhandled = {INC001, INC002, INC003}
Handled = {}
Sequence = []
Cost = 0

Initial state menjadi titik awal bagi algoritma pencarian untuk menentukan urutan penanganan.

D. Action

Action merupakan pilihan yang dapat dilakukan pada suatu state.

Pada setiap langkah, sistem memilih satu insiden yang masih berada dalam daftar unhandled untuk menjadi insiden berikutnya dalam urutan penanganan.

Contoh action:

Pilih INC002 sebagai insiden berikutnya.

Action tersebut dianggap valid selama INC002 masih berada dalam daftar insiden yang belum dipilih.

E. Transition Model

Transition model menjelaskan perubahan state setelah suatu action dilakukan.

Ketika sebuah insiden dipilih, perubahan yang terjadi adalah:

Insiden dihapus dari daftar unhandled.
Insiden ditambahkan ke daftar handled.
Insiden ditambahkan ke sequence.
Accumulated path cost diperbarui sesuai dengan cost dari keputusan tersebut.

Contoh:

State awal:

Unhandled = {INC001, INC002, INC003}
Handled = {}
Sequence = []
Cost = 0

Action:

Pilih INC002

State berikutnya:

Unhandled = {INC001, INC003}
Handled = {INC002}
Sequence = [INC002]
Cost = cost dari langkah tersebut

Proses tersebut dilakukan berulang sampai seluruh insiden memiliki posisi dalam urutan penanganan.

F. Goal Test

Goal test digunakan untuk menentukan apakah proses pencarian telah selesai.

Goal tercapai apabila:

tidak ada lagi insiden dalam daftar unhandled;
seluruh insiden telah masuk ke dalam sequence;
sequence telah membentuk urutan penanganan seluruh insiden.

Contoh goal state:

Unhandled = {}
Handled = {INC001, INC002, INC003}
Sequence = [INC002, INC001, INC003]

Urutan tersebut kemudian dapat digunakan sebagai rekomendasi penanganan insiden.

G. Path Cost

Path cost digunakan untuk merepresentasikan penalty atau biaya dari keputusan urutan penanganan yang dipilih.

Cost dalam masalah ini tidak hanya menunjukkan insiden mana yang dipilih, tetapi juga mempertimbangkan dampak dari posisi dan keterlambatan penanganan suatu insiden dalam urutan.

Beberapa komponen yang dapat dipertimbangkan dalam path cost adalah:

- `urgency`
- `impact`
- `affected_users`
- `service_criticality`
- `waiting_time_min`
- `estimated_handling_time_min`

Insiden dengan urgency, impact, jumlah pengguna terdampak, atau service criticality yang tinggi perlu diperhatikan agar tidak mengalami keterlambatan penanganan yang tidak sesuai.

Waiting time juga dapat dipertimbangkan agar insiden yang sudah menunggu lebih lama tidak terus tertunda.

Estimated handling time dapat digunakan sebagai informasi tambahan untuk melihat kebutuhan waktu penanganan dari suatu urutan.

Pada tahap Milestone 1, komponen tersebut masih berupa kandidat dan belum ditetapkan menjadi rumus atau bobot final. Penentuan cost function final perlu direview lebih lanjut oleh tim.

H. Example State Space

Untuk menggambarkan state space, digunakan tiga contoh insiden:

INC001
INC002
INC003

Dari initial state tersebut, sistem memiliki beberapa pilihan action. Setiap pilihan akan menghasilkan state baru.

Secara sederhana, state space dapat digambarkan sebagai:

                    Initial
              {INC001, INC002, INC003}
                       |
        +--------------+--------------+
        |              |              |
      INC001          INC002         INC003
        |              |              |
    +---+---+      +---+---+      +---+---+
    |       |      |       |      |       |
  INC002  INC003 INC001  INC003 INC001  INC002
    |       |      |       |      |       |
  INC003  INC002 INC003  INC001 INC002  INC001

Dengan tiga insiden, terdapat enam kemungkinan urutan penanganan:

INC001 → INC002 → INC003
INC001 → INC003 → INC002
INC002 → INC001 → INC003
INC002 → INC003 → INC001
INC003 → INC001 → INC002
INC003 → INC002 → INC001

Setiap kemungkinan urutan dapat memiliki path cost yang berbeda berdasarkan karakteristik dan posisi penanganan insiden.

I. Uniform Cost Search (UCS)

Uniform Cost Search (UCS) merupakan algoritma pencarian yang memilih state berdasarkan cumulative path cost terendah.

Dalam masalah prioritisasi insiden, UCS dapat digunakan untuk mengevaluasi berbagai kemungkinan urutan penanganan berdasarkan total cost yang telah terbentuk.

Secara konseptual, proses UCS adalah:

1. Mulai dari initial state.
2. Menghasilkan beberapa kemungkinan action.
3. Menghasilkan state baru dari setiap action.
4. Menghitung cumulative path cost setiap state.
5. Memilih state dengan cumulative path cost paling rendah untuk dikembangkan berikutnya.
6. Mengulangi proses sampai goal state ditemukan.

UCS tidak menggunakan heuristic. Pemilihan state didasarkan pada cost yang telah diperoleh dari initial state sampai state saat ini.

J. A* Search

A* merupakan algoritma pencarian yang menggunakan cumulative cost dan estimasi cost menuju goal.

Fungsi evaluasi A* dapat dituliskan sebagai:

f(n) = g(n) + h(n)

Keterangan:

g(n) adalah cumulative cost dari initial state menuju state saat ini.
h(n) adalah estimasi cost dari state saat ini menuju goal.
f(n) adalah nilai evaluasi yang digunakan untuk memilih state.

Pada masalah prioritisasi insiden, heuristic dapat digunakan untuk memperkirakan penalty yang masih mungkin terjadi dari insiden yang belum masuk ke dalam urutan.

Namun, pada Milestone 1 heuristic A* belum ditentukan secara final. Heuristic perlu dirancang dan direview terlebih dahulu agar sesuai dengan karakteristik masalah.

K. Perbandingan Awal UCS vs A*
Aspek	UCS	A*
Menggunakan path cost	Ya	Ya
Membutuhkan heuristic	Tidak	Ya
Dasar pemilihan state	Cumulative cost	Cumulative cost + heuristic
Kompleksitas perancangan	Lebih sederhana	Lebih kompleks karena membutuhkan heuristic
Penggunaan pada proyek	Dapat digunakan sebagai baseline	Dapat digunakan jika heuristic tersedia

Pada tahap ini belum ditentukan algoritma final yang akan digunakan. Pemilihan antara UCS dan A* dapat dilakukan setelah cost function dan heuristic direview.

L. Relation to Project Output

Search problem formulation menjadi dasar bagi sistem untuk menghasilkan rekomendasi urutan prioritas penanganan insiden jaringan.

State menggambarkan kondisi urutan yang sedang dibangun, action menentukan insiden berikutnya, transition menjelaskan perubahan state, dan goal menunjukkan bahwa seluruh insiden telah memiliki urutan penanganan.

Path cost digunakan untuk merepresentasikan penalty dari keputusan urutan penanganan. Dengan struktur tersebut, UCS atau A* dapat digunakan untuk mencari urutan yang sesuai dengan tujuan prioritisasi.

Output dari proses pencarian berupa rekomendasi urutan penanganan insiden. Rekomendasi tersebut dapat membantu pihak yang bertanggung jawab dalam menentukan insiden yang perlu ditangani terlebih dahulu.

M. Conclusion

Masalah prioritisasi insiden jaringan kampus dapat direpresentasikan sebagai search problem karena terdapat beberapa kemungkinan urutan penanganan yang dapat dipilih.

Formulasi search problem terdiri dari state, initial state, action, transition model, goal test, dan path cost. State menggambarkan urutan yang sedang dibangun, action memilih insiden berikutnya, dan goal tercapai ketika seluruh insiden telah memiliki urutan.

Path cost digunakan untuk merepresentasikan penalty dari keputusan urutan penanganan. UCS dapat digunakan berdasarkan cumulative path cost, sedangkan A* menggunakan cumulative path cost dan heuristic.

Pada Milestone 1, UCS dan A* masih berada pada tahap analisis. Cost function final dan heuristic A* final belum ditentukan. Keduanya akan dipilih setelah komponen cost dan heuristic direview oleh tim.