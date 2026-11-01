"""Central configuration for whisper-transcriber.

Every user-tunable value lives here. Edit this file to change default
behavior without touching the logic in `lib/`; most values can also be
overridden per run via CLI flags (see `lib/cli.py`).
"""
from __future__ import annotations

APP_NAME = "whisper-transcriber"
VERSION = "1.0.0"

# --- Project exit codes (126/127 are reserved by the shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5

# --- Whisper defaults ---
# "large" mirrors the original Colab notebook, which assumed a free GPU.
# On CPU-only machines prefer --model small/turbo (much faster).
DEFAULT_MODEL = "large"
AVAILABLE_MODELS = (
    "tiny", "tiny.en", "base", "base.en", "small", "small.en",
    "medium", "medium.en", "large", "large-v1", "large-v2", "large-v3",
    "turbo", "large-v3-turbo",
)
DEFAULT_TASK = "transcribe"
AVAILABLE_TASKS = ("transcribe", "translate")  # translate: always into English
DEFAULT_OUTPUT_FORMAT = "all"
CONCRETE_FORMATS = ("txt", "vtt", "srt", "tsv", "json")  # "all" expands to these
OUTPUT_FORMATS = CONCRETE_FORMATS + ("all",)

# --- Output locations ---
DEFAULT_OUTPUT_DIR = "."  # the Colab original wrote next to the notebook
# Tag inserted before the extension of translated outputs (audio.en.srt) so a
# later `--task translate` run can never clobber the transcription files.
TRANSLATION_TAG = "en"

# --- URL audio download (yt-dlp) ---
DOWNLOAD_AUDIO_FORMAT = "mp3"
# %(id)s keeps names collision-free; --restrict-filenames (see downloader)
# avoids shell-hostile characters in titles.
YTDLP_OUTPUT_TEMPLATE = "%(title).80s [%(id)s].%(ext)s"
# The original example links carried &list=... playlists, which made yt-dlp
# fetch every entry; download only the referenced video by default.
YTDLP_NO_PLAYLIST = True
URL_PREFIXES = ("http://", "https://")

# --- Subtitle shortening ---
DEFAULT_MAX_LINE_LENGTH = 37  # BBC subtitling guideline, kept from the original
SHORTENED_SUFFIX = "_acortado"

# --- Logging ---
LOG_FILE = None  # e.g. "whisper_transcriber.log" for a persistent audit trail
USE_COLOR = True  # ANSI colors on TTYs; auto-disabled for pipes and NO_COLOR
ANSI_RESET = "\033[0m"
LEVEL_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[32m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
}

# --- Language catalog (code -> Spanish name) ---
# Full set accepted by Whisper. The original notebook shipped a 47-entry
# dropdown that stopped at Korean (missing pt/ru/zh/nl/pl/tr/uk...) and used
# the deprecated Google code 'iw' for Hebrew, which Whisper rejects ('he').
SUPPORTED_LANGUAGES = {
    "af": "Afrikáans", "am": "Amárico", "ar": "Árabe", "as": "Asamés",
    "az": "Azerbaiyano", "ba": "Baskir", "be": "Bielorruso", "bg": "Búlgaro",
    "bn": "Bengalí", "bo": "Tibetano", "br": "Bretón", "bs": "Bosnio",
    "ca": "Catalán", "cs": "Checo", "cy": "Galés", "da": "Danés",
    "de": "Alemán", "el": "Griego", "en": "Inglés", "es": "Español",
    "et": "Estonio", "eu": "Vasco", "fa": "Persa", "fi": "Finés",
    "fo": "Feroés", "fr": "Francés", "gl": "Gallego", "gu": "Guyaratí",
    "ha": "Hausa", "haw": "Hawaiano", "he": "Hebreo", "hi": "Hindi",
    "hr": "Croata", "ht": "Criollo haitiano", "hu": "Húngaro", "hy": "Armenio",
    "id": "Indonesio", "is": "Islandés", "it": "Italiano", "ja": "Japonés",
    "jw": "Javanés", "ka": "Georgiano", "kk": "Kazajo", "km": "Jemer",
    "kn": "Canarés", "ko": "Coreano", "la": "Latín", "lb": "Luxemburgués",
    "ln": "Lingala", "lo": "Lao", "lt": "Lituano", "lv": "Letón",
    "mg": "Malgache", "mi": "Maorí", "mk": "Macedonio", "ml": "Malayalam",
    "mn": "Mongol", "mr": "Maratí", "ms": "Malayo", "mt": "Maltés",
    "my": "Birmano", "ne": "Nepalí", "nl": "Neerlandés",
    "nn": "Noruego (nynorsk)", "no": "Noruego", "oc": "Occitano",
    "pa": "Panyabí", "pl": "Polaco", "ps": "Pastún", "pt": "Portugués",
    "ro": "Rumano", "ru": "Ruso", "sa": "Sánscrito", "sd": "Sindhi",
    "si": "Cingalés", "sk": "Eslovaco", "sl": "Esloveno", "sn": "Shona",
    "so": "Somalí", "sq": "Albanés", "sr": "Serbio", "su": "Sundanés",
    "sv": "Sueco", "sw": "Suajili", "ta": "Tamil", "te": "Télugu",
    "tg": "Tayiko", "th": "Tailandés", "tk": "Turcomano", "tl": "Tagalo",
    "tr": "Turco", "tt": "Tártaro", "uk": "Ucraniano", "ur": "Urdu",
    "uz": "Uzbeko", "vi": "Vietnamita", "yi": "Yidis", "yo": "Yoruba",
    "yue": "Cantonés", "zh": "Chino",
}
