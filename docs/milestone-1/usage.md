# Panduan penggunaan Milestone 1

Detail berikut dipindahkan dari README utama tanpa mengubah implementasi.

```bash
uv run --locked proyek-certan --input data/sample_incidents.json
```

## Hasil Milestone 1

Data contoh menghasilkan perbandingan berikut:

| Metode | Weighted-minute penalty |
|---|---:|
| UCS | 1412.5903 |
| FIFO | 1531.3458 |

- Selisih biaya: **118.7556**
- Pengurangan biaya: **7.75%**
- State UCS yang diperluas: **4095**

Urutan rekomendasi UCS:

```text
INC011 -> INC006 -> INC004 -> INC003 -> INC002 -> INC008
-> INC010 -> INC005 -> INC007 -> INC001 -> INC012 -> INC009
```

CLI menampilkan rincian lengkap untuk setiap insiden, termasuk *importance
score*, waktu selesai, *step cost*, total cost, dan statistik pencarian.

### Milestone 1

<details>
<summary><strong>Format data insiden</strong></summary>

Input berupa array JSON nonkosong. Setiap insiden memiliki sembilan atribut:

| Atribut | Aturan |
|---|---|
| `incident_id` | string unik dengan format `INCxxx` |
| `category` | string nonkosong |
| `location` | string nonkosong |
| `urgency` | integer 1-5 |
| `impact` | integer 1-5 |
| `affected_users` | integer >= 0 |
| `service_criticality` | integer 1-5 |
| `waiting_time_min` | integer >= 0 |
| `estimated_handling_time_min` | integer > 0 |

Contoh:

```json
[
  {
    "incident_id": "INC001",
    "category": "wifi_slow",
    "location": "Ruang Kelas",
    "urgency": 2,
    "impact": 2,
    "affected_users": 15,
    "service_criticality": 2,
    "waiting_time_min": 35,
    "estimated_handling_time_min": 20
  }
]
```

</details>

<details>
<summary><strong>Importance score dan bobot</strong></summary>

Normalisasi dilakukan terhadap batch yang sedang diproses:

```text
normalized_urgency     = urgency / 5
normalized_impact      = impact / 5
normalized_criticality = service_criticality / 5
normalized_users       = affected_users / max_affected_users
normalized_waiting     = waiting_time_min / max_waiting_time
```

Jika maksimum jumlah pengguna atau waktu tunggu adalah nol, nilai normalisasi
komponen tersebut menjadi nol.

| Komponen | Bobot |
|---|---:|
| Urgency | 0.30 |
| Impact | 0.25 |
| Service criticality | 0.20 |
| Affected users | 0.15 |
| Waiting time | 0.10 |

```text
importance_score =
    0.30 * normalized_urgency
  + 0.25 * normalized_impact
  + 0.20 * normalized_criticality
  + 0.15 * normalized_users
  + 0.10 * normalized_waiting
```

Bobot dapat dikonfigurasi, tetapi harus nonnegatif dan berjumlah `1.0`. Bobot
baseline ini belum dikalibrasi menggunakan data operasional.

Waktu tunggu menjadi mekanisme *aging* agar laporan lama tidak terus tertunda.
`category` dan `location` hanya digunakan sebagai konteks.

</details>

<details>
<summary><strong>Perhitungan path cost</strong></summary>

```text
completion_time = elapsed_time + estimated_handling_time
step_cost       = importance_score * completion_time
total_cost      = sum(step_cost)
```

UCS mencari urutan dengan `total_cost` minimum. Nilai ini merupakan
*weighted-minute penalty*, bukan biaya finansial. FIFO memakai fungsi biaya yang
sama sebagai pembanding agar hasil keduanya dapat dievaluasi secara adil.

</details>

<details>
<summary><strong>Mengubah bobot melalui CLI</strong></summary>

```bash
uv run proyek-certan \
  --input data/sample_incidents.json \
  --weight-urgency 0.35 \
  --weight-impact 0.25 \
  --weight-service-criticality 0.20 \
  --weight-affected-users 0.10 \
  --weight-waiting-time 0.10
```

</details>

