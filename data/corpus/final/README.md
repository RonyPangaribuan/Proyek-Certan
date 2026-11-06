# Korpus final aktif CERTAN T03

Direktori ini adalah satu-satunya input korpus resmi pipeline sekarang. Tepat
15 TXT dan [knowledge_chunks.json](knowledge_chunks.json) disalin **identik byte**
dari reviewed-v3, profil `v3_t96_w10`: 487 chunk, maksimum 96 token termasuk
special tokens, overlap yang diminta 10 kata. Tidak dilakukan re-cleaning,
re-chunking, perubahan chunk ID atau penulisan ulang metadata.

[manifest.json](manifest.json) memuat path aktif, asal, SHA-256, provenance,
hak penggunaan, status publikasi dan konfigurasi tunggal. `active_text_file`
menunjuk TXT aktif di sini. `metadata.text_file` pada chunk tetap menunjuk asal
reviewed-v3 untuk menjaga bytes dan keterlacakan historis. PDF asli tetap di
[raw](../raw/); salinan historis tetap di [processed](../processed/README.md).

```bash
uv run --locked python -m proyek_certan.knowledge.final_cli verify
uv run --locked python -m proyek_certan.knowledge.final_cli index
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Diagnosis DNS pada klien" --document-level --top-k 5
```

Jalankan dari root repository. Database resmi `.local/chroma-corpus-final`
dibuat dari berkas di sini; cache model `.cache/models`. DOC-09/10 tetap
**DRAFT**; korpus ini bukan SOP lokal yang disahkan. Batas dan hasil ada dalam
[panduan M3](../../../docs/milestone-3/README.md).
