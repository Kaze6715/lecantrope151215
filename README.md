# AI Anti-Sweep Trading System for XAUUSD (Exness MT5)

## Struktur Modular

```
ai-anti-sweep/
│
├── config.py                  # Konfigurasi sistem dan parameter
├── data_handler.py            # Handler koneksi dan penarikan data MT5
├── price_action_analyzer.py   # Modul analisis price action (30 pts)
├── multi_timeframe_analyzer.py# Modul multi-TF confluence (35 pts)
├── volume_analyzer.py         # Modul volume anomaly (20 pts)
├── statistical_analyzer.py    # Modul statistical pattern (20 pts)
├── velocity_analyzer.py       # Modul velocity & acceleration (25 pts)
├── microstructure_analyzer.py # Modul microstructure (25 pts)
├── market_context_analyzer.py # Modul market context (25 pts)
├── smart_money_analyzer.py    # Modul smart money (30 pts)
├── liquidity_analyzer.py      # Modul liquidity mapping (35 pts)
├── signal_aggregator.py       # Agregator scoring & pengambilan keputusan
├── trade_executor.py          # Eksekusi trade, SL/TP, & risk mgmt
└── main.py                    # Entry point script utama
```

---

## Cara Pakai Singkat

1. **Isi `config.py`**: Atur parameter broker, risk, symbol dsb.
2. **Jalankan MT5 Terminal**: Pastikan sudah login ke akun demo/real Exness.
3. **Install dependensi**:  
   ```
   pip install MetaTrader5 pandas numpy
   ```
4. **Jalankan script utama**:  
   ```
   python main.py
   ```
5. **Cek hasil log trading & analisis** (log otomatis ke file/console).

---

## main.py (Entry Point)

```python name=main.py
import logging
import time
from config import SYSTEM_CONFIG
from data_handler import DataHandler
from signal_aggregator import SignalAggregator
from trade_executor import TradeExecutor

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler()]
    )
    data_handler = DataHandler(SYSTEM_CONFIG)
    aggregator = SignalAggregator(SYSTEM_CONFIG)
    executor = TradeExecutor(SYSTEM_CONFIG)

    if not data_handler.initialize_mt5():
        logging.error("MT5 initialization failed, exit.")
        exit(1)

    logging.info("AI Anti-Sweep System started.")

    while True:
        try:
            signal = aggregator.get_aggregated_signal(data_handler)
            logging.info(f"Signal: {signal.signal_type} | Score: {signal.total_score:.2f} | Valid: {signal.is_valid}")
            if signal.is_valid:
                result = executor.execute_trade(signal)
                logging.info(f"Trade Result: {result['message']}")
            else:
                logging.info("No valid setup. Waiting...")
            time.sleep(10)  # Adjust as needed
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(30)
```

---

## Catatan Testing & Pengembangan

- **Backtest**: Untuk analisis, gunakan export data OHLCV ke CSV lalu panggil modul2 di atas secara batch.
- **Forward test**: Jalankan di akun demo, cek log, dan validasi entry-exit logic.
- **Debugging**: Set `logging.basicConfig(level=logging.DEBUG,...)` untuk verbose log dan cek setiap scoring.
- **Tuning**: Ubah threshold komponen pada `SignalAggregator` & `config.py`.

---

**Selamat!** Dengan semua file yang sudah kamu punya (dan kode aggregator + executor di atas), sistemmu sudah siap forward-test dan dioptimasi lebih lanjut.

Jika mau contoh file `config.py` atau ingin saran optimasi/kustom logika entry, silakan bilang!