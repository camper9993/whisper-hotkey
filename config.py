# Горячая клавиша для записи (toggle)
# Первое нажатие — начать запись, второе — остановить и распознать
HOTKEY = "f12"

# Модель Whisper: tiny, base, small, medium, large-v3
# large-v3 — лучшее качество, на RTX 4070 Ti Super работает быстро
MODEL_SIZE = "large-v3"

# Устройство: "cuda" для GPU, "cpu" для процессора
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

# Частота дискретизации микрофона
SAMPLE_RATE = 16000

# Язык: None = автоопределение, "ru" = только русский, "en" = только английский
LANGUAGE = None

# Звуковая индикация (частота в Гц и длительность в мс)
BEEP_START_FREQ = 800
BEEP_START_DURATION = 150
BEEP_STOP_FREQ = 400
BEEP_STOP_DURATION = 150
