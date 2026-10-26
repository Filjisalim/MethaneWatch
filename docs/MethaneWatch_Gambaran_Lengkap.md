# MethaneWatch: Gambaran Lengkap Ide

> Dokumen kerja untuk pendaftaran MAJU:ON University Track 2026-27 (batas form: 27 Oktober 2026, 23.59 WIB).
> Penanda: **[Sumber]** = ada rujukan di bagian Sumber. **[Hipotesis]** = dugaan yang harus divalidasi. **[Verifikasi]** = pengetahuan umum yang perlu dicek ke datasheet, dosen, atau pengelola sebelum dijadikan klaim. **[Isi]** = harus diisi tim dengan fakta nyata.

---

## 1. Ringkasan satu paragraf

MethaneWatch adalah sistem dua tahap untuk TPA. **Tahap 1 (Ukur):** jaringan node sensor gas murah bertenaga surya dengan komunikasi LoRa memetakan konsentrasi metana, tren harian, dan peringatan keselamatan di satu TPA. **Tahap 2 (Manfaatkan):** dari data itu, model memperkirakan potensi gas yang bisa dimanfaatkan beserta ketidakpastiannya, mengusulkan titik ekstraksi, dan menilai opsi paling layak: pembakaran terkendali, bahan bakar kompor untuk warga sekitar, atau listrik. Lokasi pilot yang diusulkan: TPA Air Dingin, Kota Padang.

**Kalimat inti untuk juri:** *pemerintah daerah tidak bisa menurunkan atau memanfaatkan metana yang tidak pernah mereka ukur. MethaneWatch membuat pengukuran itu murah, tepercaya, dan langsung diterjemahkan menjadi keputusan.*

---

## 2. Latar belakang dan masalah

### 2.1 Masalah inti: emisi metana TPA tidak terukur
- Banyak TPA di Indonesia, terutama di luar kota besar, tidak memiliki peralatan pemantauan, tenaga terlatih, maupun anggaran rutin untuk mengukur emisi metana secara akurat. Emisi lebih sering diperkirakan lewat model. **[Sumber 1]**
- Inisiatif SMART Waste Indonesia (WRI) baru mengukur emisi di lima lokasi TPA sebagai percontohan, untuk menyusun pendekatan standar ukur, catat, dan lapor yang bisa ditiru pemda lain. Artinya bidang ini sedang dibentuk dan masih terbuka. **[Sumber 1]**

### 2.2 Skala masalah
- Komposisi sampah di TPA Indonesia masih didominasi material organik, sekitar 63 persen. **[Sumber 2]**
- Potensi emisi metana nasional dari sektor ini diperkirakan sekitar 21 juta ton CO₂ ekuivalen, sementara target ENDC penurunan emisi sektor limbah sebesar 40 juta ton. **[Sumber 2]**
- Kebijakan nasional kini melarang pembuangan sampah organik langsung ke TPA. **[Sumber 2]**
- Sektor sampah sering dianggap tidak menguntungkan sehingga APBD tidak mampu mendanai infrastruktur pengolahan ideal. **[Sumber 2]** Ini sekaligus menjadi tantangan model bisnis (lihat bagian 11).

### 2.3 Risiko keselamatan dan kesehatan
- Gas TPA berisi sekitar 45-60 persen CH₄ ditambah gas lain seperti H₂S. Sebuah studi risiko kesehatan di TPA Air Dingin menilai pekerjanya berpotensi mengalami gangguan kesehatan akibat pajanan gas tersebut. **[Sumber 3]**
- Metana yang menumpuk dan tidak dikelola berisiko memicu kebakaran atau ledakan. **[Sumber 4]**

### 2.4 Konteks lokal: TPA Air Dingin, Kota Padang
- Sebuah studi menyebut TPA ini masih open dumping dan menerima sekitar 607 ton sampah per hari; studi yang sama memproyeksikan potensi emisi metana 2020-2031. **[Sumber 5]** Tahun data dan kondisi terbaru **perlu dikonfirmasi** ke pengelola, karena bisa sudah berubah.
- Ada riset Unand (2011) yang mengukur konsentrasi CH₄ di udara ambien kawasan TPA ini, dengan nilai lebih tinggi di zona aktif daripada di permukiman sekitar. **[Sumber 6]** Ini bisa dijadikan titik rujukan sejarah (bukan pembanding langsung, karena metodenya berbeda), dan peneliti atau dosen terkait bisa menjadi mitra.

---

## 3. Pengguna dan pemangku kepentingan

| Peran | Kebutuhan (hipotesis) | Cara menguji |
|---|---|---|
| **Pengelola TPA** | Data keselamatan, tahu di mana gas menumpuk, alat yang tahan lapangan | Wawancara dan kunjungan |
| **Dinas Lingkungan Hidup (DLH)** | Data untuk pelaporan dan prioritas program, tanpa alat mahal | Wawancara |
| **Pekerja dan pemulung** | Peringatan saat kadar berbahaya | Observasi, wawancara singkat |
| **Warga sekitar** | Manfaat langsung (misalnya bahan bakar memasak), bukan hanya data | Wawancara |
| **Dosen teknik lingkungan/kimia/mesin** | Mitra teknis untuk penangkapan dan pemurnian gas | Audiensi |

**Hipotesis [Hipotesis]:** pengguna pertama adalah pengelola TPA dan DLH. Yang belum diketahui: siapa yang memutuskan dan membayar pemantauan di tingkat daerah.

---

## 4. Solusi: cara kerja sistem

### 4.1 Tahap 1: Ukur
Beberapa node sensor ditempatkan di titik terpilih (zona aktif, zona lama, batas area, dekat permukiman). Setiap node mengukur:
- konsentrasi CH₄ (dan H₂S sebagai opsi untuk keselamatan)
- suhu dan kelembapan udara (untuk koreksi sensor)
- kecepatan dan arah angin (di satu atau dua titik)

**Keluaran:** peta konsentrasi, tren harian, peringatan keselamatan, dan laporan ringkas yang bisa dicetak atau diekspor.

### 4.2 Tahap 2: Manfaatkan
Dari data pengukuran:
1. Memperkirakan **potensi gas yang bisa dimanfaatkan**, dengan rentang ketidakpastian.
2. Mengusulkan **titik ekstraksi** yang paling menjanjikan.
3. Menilai **opsi pemanfaatan** (bagian 7) dan merekomendasikan yang paling layak untuk kondisi TPA tersebut.

### 4.3 Tahap 3: Demonstrasi skala kecil (bersyarat)
Hanya jika izin dan mitra teknik tersedia: satu demonstrasi pemanfaatan yang aman dan kecil (misalnya satu titik ventilasi dengan pemurnian sederhana dan pembakar atau kompor). Jika izin di TPA belum keluar, alternatif adalah demo biodigester skala meja untuk menunjukkan jalur pemanfaatan.

### 4.4 Batas klaim (penting untuk kredibilitas)
- Sistem **tidak mengklaim total emisi**. Konsentrasi di suatu titik berbeda dari laju emisi; menghitung emisi butuh data fluks dan pemodelan. **[Verifikasi]**
- Sistem **tidak mengklaim potensi listrik** sebelum ada data debit dan kualitas gas dari lapangan.
- Keluaran yang dijanjikan: **peta konsentrasi, tren, estimasi potensi dengan ketidakpastian, dan perbandingan opsi.**

---

## 5. Arsitektur teknis

```
[Node sensor di TPA]  --LoRa-->  [Gateway]  --internet atau lokal-->  [Server/dashboard]
  CH4, suhu, RH, (H2S)            buffer data                          peta, tren, alarm,
  panel surya + baterai           offline-first                         laporan, model AI
```

### 5.1 Node sensor
- **Mikrokontroler:** ESP32 atau sejenis berdaya rendah. **[Verifikasi]**
- **Sensor gas:** MQ-4 atau sejenisnya murah, tetapi sensor oksida logam ini dikenal sensitif terhadap suhu, kelembapan, gas lain, dan mengalami drift. **[Verifikasi dengan datasheet dan dosen]** Karena itu rencana:
  - gunakan sensor murah untuk **sebaran** (banyak titik),
  - tambahkan **satu sensor referensi yang lebih akurat** (misalnya jenis NDIR, **[Verifikasi]** ketersediaan dan harga) sebagai acuan kalibrasi,
  - kalibrasi berkala.
- **Sensor pendukung:** suhu dan kelembapan (untuk koreksi), angin (anemometer) pada titik tertentu.
- **Daya:** panel surya kecil dan baterai, dengan mode tidur untuk menghemat daya.
- **Casing:** tertutup, tahan air dan debu. Perhatikan keselamatan: metana mudah terbakar, jadi hindari komponen yang menimbulkan percikan di area berkadar tinggi. **[Verifikasi]**

### 5.2 Komunikasi
- **LoRa** untuk jangkauan luas dan daya rendah di area TPA yang luas. **[Verifikasi]** jangkauan sebenarnya di medan TPA.
- **Gateway** menyimpan data sementara saat koneksi terputus, lalu mengirim ketika tersambung (offline-first).

### 5.3 Perangkat lunak
- Penyimpanan data berderet waktu, dashboard peta dan tren, aturan alarm, ekspor laporan.
- Log pengukuran dengan stempel waktu dan identitas sensor agar riwayat bisa ditelusuri.

---

## 6. Peran AI (tiga modul, dari paling dasar ke paling lanjut)

### 6.1 Modul A: Koreksi dan kalibrasi sensor
- **Masalah:** sensor murah melenceng karena suhu, kelembapan, dan usia.
- **Pendekatan:** model koreksi (misalnya regresi) yang mengkompensasi suhu dan kelembapan, dikalibrasi terhadap sensor referensi pada periode tertentu. Pemantauan drift: pembacaan yang menyimpang dari tren sensor lain ditandai.
- **Validasi:** bandingkan pembacaan terkoreksi dengan sensor referensi; laporkan galat sebelum dan sesudah koreksi.

### 6.2 Modul B: Deteksi anomali
- **Tujuan:** menandai lonjakan konsentrasi, sensor macet, dan pembacaan tidak wajar.
- **Pendekatan:** aturan statistik sederhana (ambang adaptif, z-score) lebih dulu, lalu dibandingkan dengan metode ringan seperti Isolation Forest.
- **Validasi:** injeksi gangguan pada data uji (sensor macet, lonjakan buatan) dan hitung tingkat alarm palsu dan terdeteksi.

### 6.3 Modul C: Peta spasial dan estimasi potensi gas
- **Tujuan:** memetakan area kumpulan gas dari data titik yang terbatas, dan memperkirakan potensi gas yang bisa dimanfaatkan.
- **Pendekatan:** interpolasi spasial (misalnya kriging atau regresi proses Gaussian) dengan data angin sebagai faktor; estimasi potensi menggabungkan data ukur dengan model emisi sampah (misalnya IPCC atau LandGEM, yang dipakai di studi-studi TPA **[Sumber 5][Verifikasi]**).
- **Catatan jujur:** modul ini yang paling berisiko karena data sedikit. Untuk 6 bulan, targetkan peta konsentrasi dan rentang ketidakpastian, bukan prediksi presisi.

---

## 7. Pilihan pemanfaatan gas

| Opsi | Prinsip | Kelebihan | Kekurangan | Status |
|---|---|---|---|---|
| **Pembakaran terkendali (flare) atau biofilter** | Mengubah metana menjadi CO₂ yang daya pemanasannya jauh lebih rendah | Cepat, menurunkan dampak iklim dan risiko kebakaran | Tidak menghasilkan pendapatan | **[Verifikasi]** |
| **Pemakaian langsung (kompor biogas)** | Gas dimurnikan lalu dipakai warga sekitar | Manfaat langsung ke masyarakat, teknologi sederhana, cocok untuk demo | Skala kecil, butuh pemurnian H₂S | Studi TPA Pakusari menyebut biogas bisa menggantikan LPG dengan pemurnian scrubber **[Sumber 4]** |
| **Listrik (genset gas)** | Gas dialirkan ke mesin pembangkit | Dampak energi besar | Butuh debit besar; studi TPA Sukawinatan Palembang menyebut sekitar 270-300 Nm³/jam pada metana 50 persen untuk 500 kW **[Sumber 7]** | Hanya gambaran skala dari TPA lain, bukan angka Padang |
| **Kurangi dari hulu** | Pisahkan dan olah sampah organik (biodigester) sebelum ke TPA | Mengurangi pembentukan metana sejak awal; sejalan dengan larangan organik ke TPA **[Sumber 2]** | Butuh perubahan sistem pengumpulan | Bisa jadi rekomendasi kebijakan dari data |

**Rekomendasi urutan (pendapat tim penulis dokumen ini, bukan fakta):**
1. Mulai dengan **keselamatan dan pembakaran terkendali** bila data menunjukkan kadar tinggi.
2. **Demonstrasi kompor** untuk bukti manfaat nyata bagi warga.
3. **Listrik** hanya jika data debit mendukung.

Rekomendasi akhir ditentukan oleh data lapangan lewat model kelayakan (bagian 6.3). Kriteria yang dinilai: debit dan kualitas gas, jarak ke pengguna, biaya, keselamatan, dan izin.

---

## 8. Keselamatan, etika, dan izin

- **Izin pengelola** wajib sebelum pemasangan apa pun. Kerja lapangan dengan pendamping.
- **Metana mudah terbakar; H₂S beracun dan korosif.** Jangan mengerjakan di area berkadar tinggi tanpa alat pelindung dan pendamping berpengalaman. **[Verifikasi]**
- **Perangkat elektronik** dipasang dalam casing tertutup dan sesuai praktik keselamatan di area berpotensi gas mudah terbakar. **[Verifikasi dengan dosen/ahli keselamatan]**
- **Peringatan keselamatan dari sistem** bersifat bantuan, bukan pengganti alat deteksi gas bersertifikat dan prosedur K3 pengelola.
- **Data warga dan pekerja:** jangan mengumpulkan data pribadi tanpa persetujuan.

---

## 9. Validasi dan indikator keberhasilan

| Area | Indikator | Target |
|---|---|---|
| Akurasi sensor | Galat pembacaan terkoreksi vs. sensor referensi | **[Isi]** setelah uji awal |
| Keandalan data | Persentase paket data yang diterima; daya tahan baterai | **[Isi]** |
| Deteksi anomali | Tingkat terdeteksi dan alarm palsu pada gangguan yang diinjeksi | **[Isi]** |
| Peta dan estimasi | Konsistensi peta antarhari; rentang ketidakpastian estimasi gas | **[Isi]** |
| Adopsi | Jumlah wawancara; surat dukungan; izin pemasangan | Lihat roadmap |

**Prinsip:** angka target ditetapkan **setelah** ada baseline dari uji awal. Jangan menulis target keberhasilan yang belum didukung data.

---

## 10. Roadmap 6 bulan (November 2026 - April 2027)

| Bulan | Kegiatan | Keluaran |
|---|---|---|
| **0 (sebelum 27 Okt)** | Hubungi dosen teknik lingkungan Unand dan DLH/TPA; wawancara singkat; kirim form | Form terkirim; catatan wawancara |
| **1** | Wawancara pengguna; izin; pemilihan sensor; uji awal sensor di lab | Daftar kebutuhan; izin/surat dukungan; data uji awal |
| **2** | Perakitan 2-3 node; firmware; LoRa dan gateway; kalibrasi awal | Node berjalan di lab |
| **3** | Uji lapangan terbatas di satu area TPA bersama pendamping; dashboard dasar | Data lapangan awal |
| **4** | Koreksi sensor, deteksi anomali, peta awal | Peta konsentrasi dan tren |
| **5** | Estimasi potensi gas dan penilaian opsi pemanfaatan | Draf laporan kelayakan |
| **6** | Laporan kelayakan; demo; keputusan lanjut atau tidak; (opsional) demonstrasi pemanfaatan kecil | Laporan dan demo |

Setiap fase berakhir dengan keputusan lanjut atau tidak lanjut, berdasarkan data dan izin.

---

## 11. Model bisnis (seluruhnya **[Hipotesis]**)

- **Pelanggan:** pengelola TPA, DLH kota/kabupaten, proyek atau program donor lingkungan.
- **Penawaran:**
  1. Langganan pemantauan per TPA (perangkat, dashboard, kalibrasi berkala).
  2. Paket kajian kelayakan pemanfaatan gas.
  3. Tahap lanjut: kemitraan implementasi pemanfaatan gas bersama mitra teknik.
- **Tantangan pendanaan:** sektor sampah sering dianggap tidak menguntungkan dan anggaran daerah terbatas **[Sumber 2]**; pengadaan pemerintah lambat. Mitigasi: mulai dari satu pilot, cari hibah, dukungan CSR, atau kerja sama program pengukuran seperti SMART Waste.
- **Harga:** belum ditetapkan. Bandingkan dengan biaya pengukuran manual dan alat komersial setelah wawancara.
- **Pendapatan saat ini:** nol.

---

## 12. Pembeda, risiko, dan kesenjangan

### 12.1 Pembeda (harus dicek ke kompetitor sebelum diklaim)
- Skala TPA dengan LoRa dan tenaga surya, bukan satu alat per titik.
- Kalibrasi ke alat referensi agar angka layak dilaporkan.
- Biaya terjangkau untuk daerah dengan anggaran terbatas.
- Keluaran yang langsung ke keputusan (potensi dan opsi pemanfaatan), bukan hanya grafik.

> Sudah ada penelitian kampus tentang IoT pemantau gas di fasilitas sampah, jadi "sensor gas plus dashboard" saja bukan pembeda. **Lakukan penelusuran kompetitor dan catat tanggal serta kata kuncinya.**

### 12.2 Risiko utama
| Risiko | Dampak | Mitigasi |
|---|---|---|
| Akurasi sensor murah | Data tidak dipercaya | Sensor referensi, kalibrasi, laporan galat jujur |
| Izin TPA tidak keluar | Tidak ada data lapangan | Mulai dari lab dan area terbuka; cari dukungan dosen/DLH |
| Keselamatan | Cedera | Pendamping, casing, prosedur K3 |
| Pembayar tidak jelas | Tidak berlanjut | Wawancara, pilot, hibah |
| Keahlian pemanfaatan gas kurang | Tahap 2-3 lemah | Mitra teknik lingkungan/kimia/mesin |
| Skala data kecil | Model tidak akurat | Klaim hanya peta dan rentang ketidakpastian |

### 12.3 Kesenjangan tim yang diakui
Pengalaman teknik lingkungan, penangkapan dan pemurnian gas, dan akses ke pengelola TPA. Rencana: gandeng dosen pembimbing dan manfaatkan coaching MAJU:ON.

---

## 13. Tim dan pembagian peran (isi nama dan fakta nyata)

| Peran | Tanggung jawab | Nama | Pengalaman | Jam/minggu |
|---|---|---|---|---|
| Ketua/arsitek sistem | Kebutuhan, arsitektur, integrasi, koordinasi mitra | [Isi] | [Isi] | [Isi] |
| Hardware dan sensor | Pemilihan sensor, perakitan, daya, casing, keselamatan perangkat | [Isi] | [Isi] | [Isi] |
| Firmware dan komunikasi | Sampling, LoRa, buffering, gateway | [Isi] | [Isi] | [Isi] |
| Analitik dan AI | Koreksi sensor, anomali, interpolasi, estimasi | [Isi] | [Isi] | [Isi] |
| Dashboard, validasi, bisnis | Dashboard, wawancara, dokumentasi, rencana pilot | [Isi] | [Isi] | [Isi] |
| Dosen pembimbing/mitra | Teknik lingkungan, keselamatan, akses | [Isi, belum tentu ada] | | |

---

## 14. Komponen anggaran (tanpa angka, karena harga harus diverifikasi)

- Node sensor: mikrokontroler, sensor CH₄, sensor suhu/RH, modul LoRa, panel surya, baterai, casing.
- Sensor referensi (pinjam dari lab bila memungkinkan, atau beli satu).
- Gateway LoRa dan server/penyimpanan data.
- Alat bantu lapangan dan perlengkapan keselamatan dasar.
- Transportasi dan dokumentasi.
- (Opsional) bahan demonstrasi pemanfaatan kecil.

Isi harga setelah survei toko dan konfirmasi peminjaman alat.

---

## 15. Daftar pertanyaan wawancara (15 menit)

**Pengelola TPA / DLH**
1. Apakah saat ini TPA ini mengukur metana atau gas lain? Dengan alat apa, seberapa sering?
2. Pernah ada kebakaran, asap, atau keluhan kesehatan pekerja terkait gas?
3. Siapa yang memutuskan dan membayar pemantauan lingkungan TPA? Berapa anggaran kasarnya?
4. Apa kewajiban pelaporan emisi atau lingkungan yang mereka hadapi?
5. Apakah ada rencana pemanfaatan gas atau pengolahan sampah organik?
6. Bolehkah kami memasang node uji kecil? Syarat izin dan keselamatannya apa?
7. Kalau data metana tersedia, keputusan apa yang akan berubah?

**Dosen teknik lingkungan/kimia/mesin**
1. Apakah sensor murah cukup untuk pemetaan sebaran, dan bagaimana kalibrasinya?
2. Bagaimana cara perkiraan potensi gas yang wajar dari data konsentrasi?
3. Apa persyaratan keselamatan untuk elektronik di area gas mudah terbakar?
4. Apakah ada data atau alat referensi yang bisa dipinjam?
5. Bersediakah menjadi pembimbing atau mitra teknik?

**Warga sekitar (opsional)**
1. Bahan bakar apa yang dipakai memasak, dan berapa biayanya per bulan?
2. Apa dampak TPA yang paling terasa?
3. Apakah akan tertarik memakai gas dari TPA jika aman?

---

## 16. Daftar periksa sebelum kirim form

- [ ] Semua **[Isi]** terisi dengan fakta nyata; tidak ada pengalaman atau angka karangan.
- [ ] Klaim "yang sudah dikerjakan" di esai 3 benar adanya.
- [ ] Penelusuran kompetitor dicatat (tanggal dan kata kunci).
- [ ] Kondisi terbaru TPA Air Dingin dikonfirmasi ke pengelola/DLH.
- [ ] Spesifikasi sensor dicek ke datasheet dan dosen.
- [ ] Tidak ada data sensitif (kesehatan, agama, politik) di esai.
- [ ] Persetujuan data pribadi dibaca dan dicentang sendiri oleh ketua tim.
- [ ] Dikirim sebelum **27 Oktober 2026, 23.59 WIB** (sebaiknya sore hari itu).

---

## Sumber

1. CNN Indonesia, "Ukur, Lalu Kurangi: Menyusun Standar Nasional Pengukuran Metana TPA" (3 Agustus 2026): https://www.cnnindonesia.com/nasional/20260803194631-21-1388173/ukur-lalu-kurangi-menyusun-standar-nasional-pengukuran-metana-tpa/amp
2. Kompas, "Mitigasi Metana Perlu Dipikul Bersama" (22 Mei 2026): https://lestari.kompas.com/read/2026/05/22/131457886/mitigasi-metana-perlu-dipikul-bersama
3. Studi risiko kesehatan pajanan CH₄ dan H₂S pada pekerja TPA Air Dingin (Undip): https://ejournal.undip.ac.id/index.php/jkli/article/download/58944/26575
4. Potensi biogas digester TPA Pakusari (ITS): https://journal.its.ac.id/index.php/sewagati/article/view/563/634
5. Analisis produksi dan potensi pemanfaatan listrik gas metana TPA Air Dingin (Jurnal UNP): https://jptk.ppj.unp.ac.id/index.php/jptk/article/view/318
6. Analisis konsentrasi gas metan di udara ambien LPA Air Dingin Kota Padang (repositori Unand, 2011): https://ios.perpusnas.go.id/Record/IOS3629.2906/TOC
7. Studi kelayakan PLTSa TPA Sukawinatan, Palembang: https://jurnal.univpgri-palembang.ac.id/index.php/ampere/article/view/1772
8. Pemanfaatan gas metana TPA (UGM): https://ugm.ac.id/?p=93567

> Angka dan klaim pada sumber 2, 5, dan 7 berasal dari artikel dan studi dengan metodologi serta tahun berbeda. Cantumkan sumber dan tahunnya di esai, jangan menyebutnya fakta pasti.
