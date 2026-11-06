# Bukti korpus historis — bukan input pipeline aktif

Semua TXT dan JSON di direktori ini dipertahankan pada path dan bytes aslinya
untuk audit SHA-256, tes regresi, provenance serta reproduksi penelitian.

| Tahap | Artefak dan fungsi |
|---|---|
| v1 | 15 TXT root; 130 chunk awal, 374 chunk 120/12, 484 chunk 96/10 |
| reviewed-v2 | [direktori](reviewed-v2/); koreksi konservatif dan ablation 486/378/412 chunk |
| reviewed-v3 | [direktori](reviewed-v3/); audit visual, metadata halaman dan ablation 487/378/413 chunk |

Salinan reviewed-v3 96/10 telah dipromosikan ke [final](../final/README.md)
tanpa perubahan byte. Profil 120/12 dan 96/0 hanya bukti ablation, bukan
alternatif korpus aktif. Salinan sumber yang identik tetap berguna karena
protokol mengunci lokasi historisnya; tidak dihapus sebagai duplikasi sia-sia.
