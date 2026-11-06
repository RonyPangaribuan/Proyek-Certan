# Anotasi relevansi T03 secara independen dan tanpa ranking

Paket JSON anotasi berisi kueri dan daftar seluruh 15 sumber yang sama untuk
setiap kueri. Tidak ada ranking, cosine, prediksi guardrail, ataupun label
penulis eksperimen. Label kosong pada template berarti **belum dianotasi**;
bukan label OOD.

## Prosedur anggota tim

1. Dua anotator mengisi salinan paket secara terpisah. Jangan membuka hasil
   benchmark atau berdiskusi tentang prediksi model sebelum anotasi selesai.
2. Baca sumber asli/teks turunan dan tentukan apakah informasi yang diminta
   didukung langsung. Catat ID dokumen, section, halaman bila dapat diverifikasi,
   dan alasan. Kesesuaian istilah saja belum cukup.
3. Pilih `supported`, `unsupported`, atau `uncertain`. Permintaan nilai IP,
   kredensial, status tiket, petugas, utilisasi aktual atau perkiraan pemulihan
   memerlukan sumber data operasional yang tidak ada dalam korpus statis.
   Permintaan prosedur **cara** mengumpulkan informasi tersebut bisa didukung.
4. Untuk pertanyaan kebijakan institusi tertentu, sumber institusi lain tidak
   dianggap relevan. DRAFT dapat mendukung pertanyaan tentang isi draf, tetapi
   tidak membuktikan bahwa suatu ketentuan telah disahkan.
5. Pertahankan semua dokumen yang mendukung langsung, termasuk pasangan sumber
   bila masing-masing memang mendukung permintaan. Jangan menandai dokumen hanya
   karena ada istilah teknis yang sama.
6. Setelah kedua salinan dikembalikan, pihak ketiga merekonsiliasi perbedaan.
   Laporkan agreement label supported/unsupported, agreement himpunan dokumen,
   jumlah uncertain dan keputusan adjudikasi. Jangan menganggap template kosong
   sebagai bukti validasi manusia.

## Format tiap anotasi

```json
{
  "query_id": "...",
  "query": "...",
  "annotator_id": null,
  "status": null,
  "relevant_documents": null,
  "evidence": [{"document_id": null, "section": null, "page": null, "reason": null}],
  "confidence": null,
  "annotated_at": null
}
```

Gunakan nomor halaman hanya jika benar-benar diperiksa. Untuk sumber HTML,
gunakan heading/section; jangan mengarang nomor halaman PDF yang berupa gambar.
Jika hasil anotasi manusia berbeda dari label sintetis yang telah dibekukan,
buat versi label dan laporan baru dengan jejak adjudikasi. Jangan menimpa 75
kueri historis atau diam-diam menulis ulang label untuk menaikkan skor.

Studi v3 tetap diberi label **sintetis, satu penulis, belum divalidasi manusia
independen** sampai paket benar-benar diisi oleh anggota tim. Final test v3
dibuat setelah kode dan parameter dibekukan, tetapi penulis sintetis tetap
mengetahui desain sistem; ini pembatasan penting terhadap klaim generalisasi.
