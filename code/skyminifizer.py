# Copyright (C) 2025-2026 VanilleIce
# All rights reserved.
#
# SkySheet File Minifier is proprietary software.
# Commercial use, redistribution, and modification are prohibited.
# See LICENSE.md for details.

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional, Set, Tuple

# ==================== Logging ====================

logger = logging.getLogger("SkyMinifizer")


def _setup_logging(log_file: Optional[Path] = None) -> None:
    """Konfiguriert Logging für CLI-Nutzung."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    if log_file is not None:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_file,
                mode='w',
                encoding='utf-8',
            )
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning(f"Could not create log file {log_file}: {e}")

    logger.setLevel(logging.INFO)


# ==================== Konstanten ====================

SUPPORTED_EXTENSIONS: Tuple[str, ...] = ('.json', '.txt', '.skysheet')
BACKUP_FOLDER_NAME = "backup"
LOG_FILE_NAME = "logfileminifizer.log"
OUTPUT_ENCODING = 'utf-8'

SYSTEM_FILES: Set[str] = {"desktop.ini", "thumbs.db", ".ds_store"}


# ==================== Statistik-Klasse ====================

class Stats:
    """Zählt alle Kategorien."""

    def __init__(self):
        self.minified = 0
        self.re_minified = 0
        self.skip_optimal = 0
        self.skip_not_json = 0
        self.skip_empty = 0
        self.skip_unknown_ext = 0
        self.skip_backup_folder = 0
        self.error_read = 0
        self.error_encoding = 0
        self.error_write = 0
        self.error_backup = 0
        self.error_unknown = 0

    def add(self, result: str) -> None:
        if result in self.__dict__:
            self.__dict__[result] += 1
        else:
            self.error_unknown += 1

    @property
    def total_errors(self) -> int:
        return (
            self.error_read
            + self.error_encoding
            + self.error_write
            + self.error_backup
            + self.error_unknown
        )

    @property
    def total_skipped(self) -> int:
        return (
            self.skip_optimal
            + self.skip_not_json
            + self.skip_empty
            + self.skip_unknown_ext
            + self.skip_backup_folder
        )

    @property
    def total_processed(self) -> int:
        return self.minified + self.re_minified


# ==================== Encoding-Erkennung ====================

def detect_encoding(file_path: Path) -> Optional[str]:
    """Erkennt die Kodierung einer Datei (mit BOM-Erkennung)."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)

        if header[:3] == b'\xef\xbb\xbf':
            return 'utf-8-sig'
        if header[:2] == b'\xff\xfe':
            return 'utf-16-le'
        if header[:2] == b'\xfe\xff':
            return 'utf-16-be'
    except OSError:
        pass

    for encoding in ('utf-8', 'utf-16-le', 'utf-16-be'):
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue

    return None


def read_file(file_path: Path, encoding: str) -> str:
    """Liest Datei mit angegebener Kodierung und entfernt BOM."""
    with open(file_path, 'r', encoding=encoding) as f:
        content = f.read()

    if content.startswith('\ufeff'):
        content = content[1:]

    return content


def write_file(file_path: Path, content: str, encoding: str = OUTPUT_ENCODING) -> None:
    """Schreibt Inhalt in Datei (UTF-8 ohne BOM)."""
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)


# ==================== Minifizierung ====================

def minify_json(content: str) -> Optional[str]:
    """Minifiziert JSON-Inhalt (sicher, via Parser)."""
    try:
        data = json.loads(content)
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    except json.JSONDecodeError as e:
        logger.error(f"[JSON ERROR] Invalid JSON structure: {e}")
        return None


def minify_content(content: str, file_ext: str) -> Optional[str]:
    """Wählt die passende Minifizierungs-Methode basierend auf Dateiendung."""
    if file_ext in ('.json', '.txt', '.skysheet'):
        return minify_json(content)

    return None


# ==================== Backup (Verschieben) ====================

def _get_backup_folder(base_dir: Path) -> Path:
    """Gibt den Backup-Ordner-Pfad zurück (erstellt ihn NICHT).

    Der Ordner wird erst erstellt, wenn tatsächlich eine Datei
    verschoben wird (in `_move_to_backup`).
    """
    return base_dir / BACKUP_FOLDER_NAME


def _move_to_backup(file_path: Path, backup_folder: Path) -> Optional[Path]:
    """Verschiebt die Original-Datei in den Backup-Ordner.

    Dies ist KEIN "Save"-Vorgang — die Datei wird verschoben,
    nicht kopiert. Der backup/-Ordner ist ein Sicherheitsnetz
    für die Originale, falls etwas schiefgeht.

    Der Ordner wird hier erstellt (falls noch nicht vorhanden).
    """
    try:
        backup_folder.mkdir(parents=True, exist_ok=True)
        backup_path = backup_folder / file_path.name

        if backup_path.exists():
            backup_path.unlink()

        shutil.move(str(file_path), str(backup_path))
        return backup_path
    except Exception as e:
        logger.error(f"[BACKUP ERROR] Could not move {file_path.name}: {e}")
        return None


# ==================== Datei-Verarbeitung ====================

def process_file(file_path: Path, backup_folder: Optional[Path] = None) -> str:
    """Verarbeitet eine einzelne Datei."""
    if not file_path.is_file():
        logger.error(f"[ERROR] File not found: {file_path}")
        return "error_read"

    file_ext = file_path.suffix.lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        logger.warning(f"[SKIP] Unsupported extension: {file_path.name}")
        return "skip_unknown_ext"

    try:
        if file_path.stat().st_size == 0:
            logger.warning(f"[SKIP] Empty file: {file_path.name}")
            return "skip_empty"
    except OSError as e:
        logger.error(f"[ERROR] Could not stat {file_path.name}: {e}")
        return "error_read"

    if backup_folder is None:
        backup_folder = _get_backup_folder(file_path.parent)

    original_encoding = detect_encoding(file_path)
    if original_encoding is None:
        logger.error(f"[ERROR] Could not detect encoding: {file_path.name}")
        return "error_encoding"

    try:
        content = read_file(file_path, original_encoding)
    except OSError as e:
        logger.error(f"[ERROR] Could not read {file_path.name}: {e}")
        return "error_read"

    minified_content = minify_content(content, file_ext)

    if minified_content is None:
        if file_ext in ('.txt', '.skysheet'):
            logger.warning(f"[SKIP] Not valid JSON, cannot minify: {file_path.name}")
        return "skip_not_json"

    if content == minified_content:
        logger.info(f"[SKIP] Already optimal: {file_path.name}")
        return "skip_optimal"

    if file_ext == '.skysheet':
        output_path = file_path
        is_re_minify = True
    else:
        output_path = file_path.with_suffix('.skysheet')
        is_re_minify = False

    backup_path = _move_to_backup(file_path, backup_folder)
    if backup_path is None:
        return "error_backup"

    try:
        write_file(output_path, minified_content, OUTPUT_ENCODING)
    except OSError as e:
        logger.error(f"[ERROR] Could not write {output_path.name}: {e}")
        return "error_write"

    if is_re_minify:
        logger.info(f"[SUCCESS] Re-minified: {output_path.name}")
    else:
        logger.info(f"[SUCCESS] Minified: {file_path.name} → {output_path.name}")
    logger.info(f"          Input Encoding: {original_encoding.upper()}")
    logger.info(f"          Output Encoding: {OUTPUT_ENCODING.upper()}")
    logger.info(f"          Original saved to: {backup_path}")

    return "re_minified" if is_re_minify else "minified"


def process_directory(
    directory: Path,
    backup_folder: Optional[Path] = None,
    stats: Optional[Stats] = None,
) -> Stats:
    """Verarbeitet alle unterstützten Dateien in einem Verzeichnis rekursiv."""
    if stats is None:
        stats = Stats()

    if backup_folder is None:
        backup_folder = _get_backup_folder(directory)

    processed: Set[Path] = set()

    logger.info(f"\nProcessing directory: {directory}")

    for root, _, files in os.walk(directory):
        root_path = Path(root)

        if BACKUP_FOLDER_NAME in root_path.parts:
            stats.add("skip_backup_folder")
            continue

        for file in files:
            file_path = root_path / file

            if file_path.name.lower() in SYSTEM_FILES:
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.warning(f"[SKIP] Unsupported extension: {file_path.name}")
                stats.add("skip_unknown_ext")
                continue

            if file_path in processed:
                continue
            processed.add(file_path)

            try:
                relative = file_path.relative_to(directory)
                file_backup_folder = backup_folder / relative.parent
            except ValueError:
                file_backup_folder = backup_folder

            result = process_file(file_path, file_backup_folder)
            stats.add(result)

    return stats


# ==================== Menü ====================

def _show_no_files_message():
    """Zeigt Anleitung, wenn keine Dateien übergeben wurden."""
    print()
    print("  ============================================================")
    print("   SkySheet File Minifier")
    print("  ============================================================")
    print()
    print("   No files were dragged onto this .exe.")
    print()
    print("   HOW TO USE:")
    print("     1. Select files or folders in Explorer")
    print("     2. Drag them onto this .exe file")
    print("     3. Choose a mode (1 = Normal, 2 = Debug)")
    print()
    print("   Supported formats:")
    print("     .json     -> minified to .skysheet")
    print("     .txt      -> minified to .skysheet (if valid JSON)")
    print("     .skysheet -> re-minified")
    print()
    print("   Original files are moved to 'backup/' only if needed.")
    print()
    print("  ------------------------------------------------------------")
    print()


def _ask_mode() -> bool:
    """Fragt den User nach dem Modus. Returns True für Debug."""
    print()
    print("  ============================================================")
    print("   SkySheet File Minifier")
    print("  ============================================================")
    print()
    print("   Files received. Choose mode:")
    print()
    print("     [1]  Normal mode  (short summary)")
    print("     [2]  Debug mode   (detailed summary)")
    print()
    print("  ------------------------------------------------------------")
    print()

    while True:
        try:
            mode = input("  Enter 1 or 2 (default: 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return False

        if not mode:
            mode = "1"

        if mode == "1":
            return False
        elif mode == "2":
            return True
        else:
            print()
            print("  [ERROR] Invalid choice. Please enter 1 or 2.")
            print()


def _pause_if_frozen():
    """Wartet auf beliebige Taste, wenn die .exe direkt gestartet wurde."""
    if not getattr(sys, 'frozen', False):
        return

    try:
        print("  Press any key to exit...", end="", flush=True)
        import msvcrt
        msvcrt.getch()  # Wartet auf einen Tastendruck (ohne Enter)
        print()  # Neue Zeile nach dem Tastendruck
    except (EOFError, KeyboardInterrupt):
        print()
        pass


# ==================== CLI ====================

def main(argv: list) -> int:
    """CLI-Einstiegspunkt."""
    is_frozen = getattr(sys, 'frozen', False)

    # --debug Flag hat Vorrang (überspringt Menü)
    debug_mode = "--debug" in argv
    argv = [arg for arg in argv if arg != "--debug"]

    # Doppelklick auf .exe (keine Dateien, kein --debug) → Anleitung
    if is_frozen and not argv and not debug_mode:
        _show_no_files_message()
        _pause_if_frozen()
        return 1

    # Drag-and-Drop (Dateien, kein --debug) → Menü
    if is_frozen and argv and not debug_mode:
        debug_mode = _ask_mode()

    # Wo liegt die .exe? (PyInstaller-safe)
    if is_frozen:
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    log_file = exe_dir / LOG_FILE_NAME

    _setup_logging(log_file)

    if len(argv) < 1:
        logger.info("SkySheet File Minifier")
        logger.info("Usage: Drag files/folders onto SkyMinifizer.exe")
        logger.info("Supported formats: .json, .txt, .skysheet")
        _pause_if_frozen()
        return 1

    stats = Stats()
    processed_paths: list = []

    backup_folder = _get_backup_folder(exe_dir)

    logger.info(f"Log file: {log_file}")
    logger.info(f"Backup folder (if needed): {backup_folder}")

    logger.info("Starting SkySheet minification...")

    for arg in argv:
        path = Path(arg).resolve()

        if not path.exists():
            logger.warning(f"\n[WARNING] Path does not exist: {path}")
            stats.error_read += 1
            continue

        processed_paths.append(str(path))

        if path.is_file():
            logger.info(f"\nProcessing file: {path.name}")
            result = process_file(path, backup_folder)
            stats.add(result)

        elif path.is_dir():
            process_directory(path, backup_folder, stats)

        else:
            logger.error(f"\n[ERROR] Unsupported path type: {path}")
            stats.error_unknown += 1

    # Abschlussbericht
    logger.info("\n" + "=" * 60)
    if debug_mode:
        logger.info("MINIFICATION SUMMARY (DEBUG)")
    else:
        logger.info("MINIFICATION SUMMARY")
    logger.info("=" * 60)

    if debug_mode:
        logger.info(f"Processed locations: {', '.join(processed_paths)}")
        logger.info("")
        logger.info(f"• Minified (json/txt → skysheet): {stats.minified}")
        logger.info(f"• Re-minified (skysheet → skysheet): {stats.re_minified}")
        logger.info(f"• Skipped (already optimal): {stats.skip_optimal}")
        logger.info(f"• Skipped (not valid JSON): {stats.skip_not_json}")
        logger.info(f"• Skipped (empty file): {stats.skip_empty}")
        logger.info(f"• Skipped (unknown extension): {stats.skip_unknown_ext}")
        logger.info(f"• Skipped (backup folder): {stats.skip_backup_folder}")
        logger.info("")
        logger.info(f"• Errors (read): {stats.error_read}")
        logger.info(f"• Errors (encoding): {stats.error_encoding}")
        logger.info(f"• Errors (write): {stats.error_write}")
        logger.info(f"• Errors (backup): {stats.error_backup}")
        logger.info(f"• Errors (unknown): {stats.error_unknown}")
        logger.info("")
        logger.info(f"• Total processed: {stats.total_processed}")
        logger.info(f"• Total skipped: {stats.total_skipped}")
        logger.info(f"• Total errors: {stats.total_errors}")
    else:
        logger.info(f"• Minified: {stats.minified} file(s)")
        logger.info(f"• Re-minified: {stats.re_minified} file(s)")
        logger.info(f"• Skipped (already optimal): {stats.skip_optimal} file(s)")
        if stats.total_errors > 0:
            logger.info(f"• Errors: {stats.total_errors}")

    logger.info("")
    if stats.total_processed > 0:
        logger.info(f"• Originals saved to: {backup_folder}")
    else:
        logger.info("• No files needed minification — backup/ not created")
    logger.info(f"• Log file: {log_file}")
    logger.info("")
    logger.info("Done!")

    _pause_if_frozen()

    return 0 if stats.total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))