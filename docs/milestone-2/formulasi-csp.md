# Formulasi Constraint Satisfaction Problem (CSP)

## 1. Pendahuluan

Pada Milestone 1, sistem digunakan untuk melakukan prioritisasi insiden jaringan berdasarkan data insiden dan algoritma pencarian. Pada Milestone 2, proses tersebut dilanjutkan dengan menentukan teknisi dan slot waktu untuk menangani setiap insiden.

Proses penugasan teknisi dimodelkan sebagai Constraint Satisfaction Problem (CSP). Data teknisi yang digunakan merupakan data sintetis untuk kebutuhan prototipe dan pengujian.

CSP pada proyek ini menggunakan tiga komponen utama:

CSP = (X, D, C)

Keterangan:
- X = Variables
- D = Domains
- C = Constraints

## 2. Variables (X)

Variable pada CSP adalah setiap insiden jaringan yang harus diberikan assignment berupa pasangan teknisi dan slot waktu.

Berdasarkan data insiden, terdapat 12 insiden:

X = {
    INC001,
    INC002,
    INC003,
    INC004,
    INC005,
    INC006,
    INC007,
    INC008,
    INC009,
    INC010,
    INC011,
    INC012
}

Setiap variable harus mendapatkan tepat satu nilai berupa pasangan:

(teknisi, slot)

Contoh:

INC001 → (TECH004, SLOT_1)

Artinya INC001 ditangani oleh TECH004 pada SLOT_1.

## 3. Domains (D)

Domain adalah kumpulan nilai yang mungkin diberikan kepada setiap variable.

Pada proyek ini, nilai domain berupa pasangan:

(teknisi, slot)

Pasangan tersebut hanya dimasukkan ke dalam domain apabila:

1. Teknisi mempunyai skill yang sesuai dengan kategori insiden.
2. Teknisi tersedia pada slot tersebut.

Constraint konflik teknisi-slot akan digunakan pada proses selanjutnya untuk memastikan satu teknisi tidak menangani dua insiden pada slot yang sama.

### 3.1 Domain INC001

Kategori INC001 adalah wifi_slow.

D(INC001) = {
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3)
}

### 3.2 Domain INC002 dan INC003

Kategori INC002 dan INC003 adalah network_down.

D(INC002) = {
    (TECH002, SLOT_1),
    (TECH002, SLOT_3),
    (TECH003, SLOT_2),
    (TECH003, SLOT_3)
}

D(INC003) = {
    (TECH002, SLOT_1),
    (TECH002, SLOT_3),
    (TECH003, SLOT_2),
    (TECH003, SLOT_3)
}

### 3.3 Domain INC004

Kategori INC004 adalah unstable_connection.

D(INC004) = {
    (TECH001, SLOT_1),
    (TECH001, SLOT_2),
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3)
}

### 3.4 Domain INC005

Kategori INC005 adalah access_point_failure.

D(INC005) = {
    (TECH001, SLOT_1),
    (TECH001, SLOT_2),
    (TECH005, SLOT_2),
    (TECH005, SLOT_3)
}

### 3.5 Domain INC006

Kategori INC006 adalah dns_issue.

D(INC006) = {
    (TECH003, SLOT_2),
    (TECH003, SLOT_3)
}

### 3.6 Domain INC007

Kategori INC007 adalah wifi_down.

D(INC007) = {
    (TECH001, SLOT_1),
    (TECH001, SLOT_2),
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3),
    (TECH005, SLOT_2),
    (TECH005, SLOT_3)
}

### 3.7 Domain INC008

Kategori INC008 adalah router_failure.

D(INC008) = {
    (TECH002, SLOT_1),
    (TECH002, SLOT_3),
    (TECH005, SLOT_2),
    (TECH005, SLOT_3)
}

### 3.8 Domain INC009

Kategori INC009 adalah gateway_unreachable.

D(INC009) = {
    (TECH002, SLOT_1),
    (TECH002, SLOT_3),
    (TECH003, SLOT_2),
    (TECH003, SLOT_3)
}

### 3.9 Domain INC010

Kategori INC010 adalah wifi_slow.

D(INC010) = {
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3)
}

### 3.10 Domain INC011

Kategori INC011 adalah unstable_connection.

D(INC011) = {
    (TECH001, SLOT_1),
    (TECH001, SLOT_2),
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3)
}

### 3.11 Domain INC012

Kategori INC012 adalah wifi_down.

D(INC012) = {
    (TECH001, SLOT_1),
    (TECH001, SLOT_2),
    (TECH004, SLOT_1),
    (TECH004, SLOT_2),
    (TECH004, SLOT_3),
    (TECH005, SLOT_2),
    (TECH005, SLOT_3)
}

## 4. Constraints (C)

Constraint digunakan untuk memastikan assignment yang dihasilkan tidak melanggar aturan yang telah ditentukan.

Pada Milestone 2 terdapat tiga constraint utama.

### 4.1 Skill Constraint

Teknisi harus mempunyai skill yang sesuai dengan kategori insiden.

Secara sederhana:

category(incident) ∈ skills(technician)

Contoh:

INC001 = wifi_slow

TECH004 dapat menangani INC001 karena TECH004 mempunyai skill wifi_slow.

Teknisi yang tidak mempunyai skill tersebut tidak dapat diberikan kepada INC001.

### 4.2 Availability Constraint

Teknisi hanya dapat menangani insiden pada slot yang terdapat pada available_slots teknisi.

Secara sederhana:

slot ∈ available_slots(technician)

Contoh:

TECH001 memiliki available_slots:

[SLOT_1, SLOT_2]

Maka:

(TECH001, SLOT_1) → valid
(TECH001, SLOT_2) → valid
(TECH001, SLOT_3) → tidak valid

### 4.3 Technician-Slot Conflict Constraint

Satu teknisi tidak boleh menangani dua insiden pada slot yang sama.

Untuk dua insiden berbeda, assignment harus memenuhi:

technician(I1) ≠ technician(I2)
OR
slot(I1) ≠ slot(I2)

Contoh tidak valid:

INC001 → (TECH004, SLOT_1)
INC010 → (TECH004, SLOT_1)

Contoh valid:

INC001 → (TECH004, SLOT_1)
INC010 → (TECH004, SLOT_2)

## 5. Jenis Constraint

Constraint pada CSP dapat dibedakan menjadi unary constraint dan binary constraint.

### 5.1 Unary Constraint

Unary constraint adalah constraint yang memeriksa satu variable.

Pada proyek ini, skill constraint dan availability constraint digunakan untuk membentuk domain setiap insiden.

### 5.2 Binary Constraint

Binary constraint adalah constraint yang melibatkan dua variable.

Pada proyek ini, binary constraint digunakan untuk memeriksa konflik teknisi dan slot antara dua insiden.

Contoh:

INC001 → (TECH004, SLOT_1)
INC010 → (TECH004, SLOT_1)

Kedua assignment tersebut tidak dapat digunakan secara bersamaan karena menggunakan teknisi dan slot yang sama.

## 6. Constraint Graph

Constraint graph digunakan untuk menggambarkan hubungan antar-variable.

Pada proyek ini:

- Node = insiden
- Edge = binary constraint antara dua insiden

Node yang digunakan adalah:

INC001, INC002, INC003, INC004,
INC005, INC006, INC007, INC008,
INC009, INC010, INC011, INC012

Setiap pasangan insiden perlu diperiksa apabila keduanya mendapatkan assignment. Pemeriksaan dilakukan untuk memastikan tidak terjadi konflik teknisi dan slot.

## 7. Partial Assignment

Partial assignment adalah kondisi ketika baru sebagian variable telah diberikan nilai.

Contoh:

INC001 → (TECH004, SLOT_1)
INC002 → (TECH002, SLOT_3)

Pada kondisi tersebut, belum semua insiden mendapatkan teknisi dan slot.

## 8. Complete Assignment

Complete assignment adalah kondisi ketika seluruh variable telah mendapatkan nilai.

Assignment disebut complete apabila seluruh 12 insiden sudah mempunyai pasangan teknisi dan slot.

## 9. Consistent Assignment

Assignment disebut consistent apabila tidak melanggar constraint yang telah ditentukan.

Contoh consistent:

INC001 → (TECH004, SLOT_1)
INC010 → (TECH004, SLOT_2)

Tidak terjadi konflik karena TECH004 digunakan pada slot yang berbeda.

Contoh tidak consistent:

INC001 → (TECH004, SLOT_1)
INC010 → (TECH004, SLOT_1)

Assignment tersebut melanggar constraint karena TECH004 mendapatkan dua insiden pada SLOT_1.

## 10. CSP Solution

CSP solution adalah assignment yang:

1. Memberikan nilai kepada seluruh variable.
2. Tidak melanggar constraint skill.
3. Tidak melanggar constraint availability.
4. Tidak memiliki konflik teknisi dan slot.

Dengan demikian, solusi CSP harus berupa complete assignment yang consistent.

## 11. AC-3

AC-3 digunakan untuk melakukan constraint propagation dengan cara mengurangi nilai yang tidak memungkinkan dari domain variable.

Tujuan AC-3 adalah mengurangi domain sebelum proses pencarian menggunakan Backtracking.

AC-3 menggunakan proses REVISE untuk memeriksa hubungan antara dua variable.

Secara sederhana:

AC-3
↓
Pilih pasangan variable
↓
REVISE
↓
Periksa nilai domain
↓
Hapus nilai yang tidak memiliki pasangan yang compatible
↓
Domain menjadi lebih kecil

### 11.1 REVISE

REVISE memeriksa apakah setiap nilai pada domain variable pertama masih mempunyai nilai yang compatible pada domain variable kedua.

Jika suatu nilai pada domain variable pertama tidak mempunyai satu pun nilai pada domain variable kedua yang memenuhi constraint konflik teknisi-slot, maka nilai tersebut dapat dihapus.

Jika terjadi penghapusan nilai, domain variable yang berhubungan perlu diperiksa kembali oleh AC-3.

### 11.2 Empty Domain

Jika setelah proses pruning sebuah domain menjadi kosong:

D(INC) = {}

maka tidak ada nilai yang dapat diberikan kepada variable tersebut.

Kondisi ini menunjukkan bahwa CSP tidak memiliki solusi untuk kondisi assignment dan domain yang sedang diperiksa.

## 12. Backtracking

Setelah domain diproses oleh AC-3, Backtracking digunakan untuk mencari complete assignment yang konsisten.

Proses dasarnya:

Pilih variable
↓
Pilih nilai dari domain
↓
Cek constraint
↓
Jika valid → lanjut ke variable berikutnya
↓
Jika tidak valid → pilih nilai lain
↓
Jika tidak ada nilai yang valid → backtrack

Backtracking digunakan karena assignment yang melanggar constraint dapat dihentikan lebih awal.

## 13. MRV

MRV atau Minimum Remaining Values digunakan untuk menentukan variable yang akan dipilih terlebih dahulu.

Variable dengan jumlah nilai domain paling sedikit dipilih terlebih dahulu.

Contoh:

INC006 = 2 nilai
INC005 = 4 nilai
INC007 = 7 nilai

Maka MRV akan memilih INC006.

Namun, jumlah domain dapat berubah setelah proses AC-3 sehingga MRV digunakan berdasarkan kondisi domain saat proses pencarian berlangsung.

## 14. LCV

LCV atau Least Constraining Value digunakan untuk menentukan urutan nilai yang akan dicoba dari domain sebuah variable.

Nilai yang paling sedikit membatasi pilihan variable lain dicoba terlebih dahulu.

Dengan demikian, LCV membantu Backtracking mencoba nilai yang masih memberikan banyak kemungkinan kepada variable lain.

## 15. Hubungan AC-3, Backtracking, MRV, dan LCV

Keempat metode digunakan secara berurutan dalam proses penyelesaian CSP.

Data Insiden
↓
Data Teknisi
↓
Pembentukan Domain
↓
AC-3
↓
Pruning Domain
↓
Backtracking
↓
MRV → memilih variable
↓
LCV → memilih urutan nilai
↓
Complete Assignment
↓
Assignment Teknisi + Slot

AC-3 berfungsi mengurangi kemungkinan yang tidak valid dari domain.

Backtracking kemudian digunakan untuk mencari solusi lengkap.

MRV membantu memilih variable yang akan diproses terlebih dahulu, sedangkan LCV membantu menentukan nilai yang dicoba terlebih dahulu.

## 16. Hubungan dengan Milestone 1

Milestone 2 merupakan kelanjutan dari Milestone 1.

Alur sistem secara umum adalah:

Data Insiden
↓
Prioritisasi Insiden
↓
UCS / hasil prioritas Milestone 1
↓
Data Teknisi
↓
Pembentukan Domain CSP
↓
AC-3
↓
Backtracking + MRV + LCV
↓
Assignment Teknisi dan Slot

Milestone 1 berfokus pada prioritisasi insiden, sedangkan Milestone 2 menambahkan proses penentuan teknisi dan slot waktu dengan menggunakan CSP.

Data dan aturan teknisi yang digunakan pada Milestone 2 merupakan data sintetis untuk kebutuhan prototipe.

## 17. Kesimpulan

Formulasi CSP pada Milestone 2 terdiri dari 12 variable yang berasal dari 12 insiden jaringan.

Setiap variable memiliki domain berupa pasangan teknisi dan slot yang memenuhi constraint skill dan availability.

Constraint utama yang digunakan adalah:

1. Teknisi harus mempunyai skill yang sesuai dengan insiden.
2. Teknisi harus tersedia pada slot yang dipilih.
3. Satu teknisi tidak boleh menangani dua insiden pada slot yang sama.

AC-3 digunakan untuk melakukan pruning domain. Setelah itu, Backtracking digunakan untuk mencari complete assignment dengan bantuan MRV dan LCV.

Dengan formulasi ini, sistem dapat menghasilkan assignment teknisi dan slot yang memenuhi constraint yang telah ditentukan pada Milestone 2.