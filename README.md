# whisper-hotkey

Windows-утилита для голосового ввода текста. Зажимаешь горячую клавишу, говоришь — текст вставляется туда, где стоит курсор.

## Возможности

- Push-to-talk: зажал клавишу — говоришь — отпустил — текст вставлен
- Локальное распознавание через [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (GPU)
- Русский + английский с автоопределением языка
- Звуковая индикация начала/конца записи
- Автоматическое восстановление буфера обмена после вставки

## Требования

- Windows 10/11
- Python 3.10+
- NVIDIA GPU с поддержкой CUDA (рекомендуется)
- Микрофон

## Установка

```bash
git clone https://github.com/camper9993/whisper-hotkey.git
cd whisper-hotkey
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

> Запускать от **администратора** — требуется для перехвата глобальных горячих клавиш.

## Настройки

Редактируй `config.py`:

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `HOTKEY` | `ctrl+shift+space` | Горячая клавиша (push-to-talk) |
| `MODEL_SIZE` | `large-v3` | Модель Whisper |
| `DEVICE` | `cuda` | `cuda` или `cpu` |
| `LANGUAGE` | `None` | `None` = авто, `"ru"`, `"en"` |
