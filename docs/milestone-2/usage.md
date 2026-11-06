# Panduan penggunaan Milestone 2

Detail berikut dipindahkan dari README utama tanpa mengubah implementasi.

```bash
uv run --locked python -m proyek_certan.constraint_solver.assignment_cli --incidents data/sample_incidents.json --technicians data/sample_technicians.json
uv run --locked python -m proyek_certan.constraint_solver.benchmark --runs 10
```

Benchmark dapat menulis CSV lokal melalui `--csv .local/benchmark_results.csv`.

## Hasil Milestone 2

Dataset utama terdiri dari 12 insiden, 5 teknisi, dan 3 slot waktu. Solver
menghasilkan status `solved`, 12 assignment, serta hasil validasi `passed`.

| Statistik | Nilai |
|---|---:|
| AC-3 arcs processed | 62 |
| AC-3 revised arcs | 0 |
| AC-3 values pruned | 0 |
| Nodes expanded | 12 |
| Assignments tried | 12 |
| Backtracks | 0 |
| Forward checks | 12 |
| Forward Checking values pruned | 29 |

AC-3 tetap memproses 62 arc. Nilai `revised arcs` dan `values pruned` sebesar
nol menunjukkan bahwa domain awal dataset utama sudah *arc-consistent*, bukan
bahwa AC-3 gagal bekerja.

Sensitivity benchmark mengevaluasi pertambahan jumlah insiden menggunakan data
dan konfigurasi solver yang sama:

| Skenario | Jumlah insiden | Status |
|---|---:|---|
| Small | 4 | solved |
| Medium | 8 | solved |
| Large | 12 | solved |

Runtime tidak dicantumkan karena hasil CSV benchmark merupakan artefak
eksperimen lokal dan tidak disimpan di repository.

### Milestone 2

#### Representasi CSP

- **Variable:** setiap insiden.
- **Domain:** pasangan `(technician, slot)` yang tersedia untuk insiden.
- **Unary filtering:** skill teknisi harus sesuai dengan kategori insiden dan
  slot harus termasuk availability teknisi.
- **Binary constraint:** dua insiden berbeda tidak boleh menggunakan pasangan
  teknisi-slot yang sama.

#### Solver pipeline

```text
AC-3 dan REVISE
    -> Backtracking
    -> MRV
    -> LCV
    -> Forward Checking
    -> validasi assignment
```

AC-3 melakukan constraint propagation sebelum pencarian. Backtracking memilih
variable dengan MRV, mengurutkan nilai menggunakan LCV, dan melakukan Forward
Checking setelah assignment sementara. Hasil akhir diperiksa kembali agar
assignment lengkap dan seluruh constraint terpenuhi.

#### Data teknisi

Data teknisi sintetis berada di `data/sample_technicians.json`. Setiap teknisi
memiliki:

- `technician_id`
- `skills`
- `available_slots`

