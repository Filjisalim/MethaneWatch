/**
 * power.h / power.cpp – Manajemen Daya
 * =====================================
 * Stub minimal untuk memonitor tegangan baterai dan mengatur level daya.
 * Prototipe awal. Belum diuji di lapangan.
 */

#pragma once
#include <stdint.h>

/** Kembalikan tegangan baterai terakhir yang dibaca (mV). */
uint16_t power_get_vbat_mv(void);

/** Kembalikan persentase baterai kasar berdasarkan tegangan Li-ion.
 *  ASUMSI: kurva tegangan-kapasitas linear 3,5 V (0%) - 4,2 V (100%).
 *  [Verifikasi: kurva nyata tidak linear. Gunakan LUT untuk akurasi lebih baik.] */
uint8_t power_get_soc_pct(uint16_t vbat_mv);
