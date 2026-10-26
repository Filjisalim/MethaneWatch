/**
 * power.cpp – Implementasi Manajemen Daya
 * Prototipe awal. Belum diuji di lapangan.
 */

#include "power.h"

uint16_t power_get_vbat_mv(void) {
    // Dibaca di sensors.cpp; disini hanya stub
    return 0;
}

uint8_t power_get_soc_pct(uint16_t vbat_mv) {
    // Asumsi: 3500 mV = 0%, 4200 mV = 100% [Verifikasi kurva nyata baterai]
    if (vbat_mv <= 3500) return 0;
    if (vbat_mv >= 4200) return 100;
    return (uint8_t)((vbat_mv - 3500) * 100 / 700);
}
