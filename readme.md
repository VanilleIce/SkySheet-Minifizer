# SkySheet File Minifier

A standalone tool that minifies SkySheet files (JSON, TXT, SkySheet) to reduce file size — without needing Python installed.

---

## ✨ What does it do?

Drag files or folders onto `SkyMinifizer.exe` and it will:

1. **Minify** JSON, TXT and SkySheet files (removes whitespace)
2. **Move** the original files to a `backup/` folder (safety net)
3. **Write** the minified `.skysheet` files to the original location

No Python required — the `.exe` is fully self-contained.

---

## 🚀 Usage

### Drag & Drop (recommended)

1. Select files or folders in Explorer
2. Drag them onto `SkyMinifizer.exe`
3. Choose a mode:
   - **`1`** — Normal mode (short summary)
   - **`2`** — Debug mode (detailed summary)
4. Done! The console shows a summary.

### Double-click

Double-click `SkyMinifizer.exe` **without** dragging files → you'll see a short usage guide. This is intentional — the tool needs files to work with.

---

## 📁 What happens to my files?

| File type | What happens |
|---|---|
| **`.json`** | Minified → written as `.skysheet` |
| **`.txt`** | Minified → written as `.skysheet` (only if valid JSON) |
| **`.skysheet`** | Re-minified in place |
| **Already optimal** | Skipped (no changes, no backup) |
| **Not valid JSON** | Skipped (cannot be minified) |

**Original files** are moved to `backup/` — **only if** minification was actually performed.

**If nothing needs minification**, the `backup/` folder is **not created** (no empty folder clutter).

---

## 🛡️ The `backup/` folder — a safety net

The `backup/` folder is **not** a save folder — it's a **safety net** for your originals.

- **Original files** are moved here (not copied)
- **Minified files** are written to the original location
- **To restore an original**: copy it back from `backup/`

> ⚠️ **Note:** Existing files in `backup/` are overwritten on each run.

---

## 🔧 Supported formats

| Format | Description |
|---|---|
| `.json` | Standard Sky sheet format |
| `.txt` | Legacy format (only if valid JSON) |
| `.skysheet` | Community format |

---

## 🐛 Debug mode

Choose **`2`** in the menu, or run from the command line:

```cmd
SkyMinifizer.exe --debug file1.json file2.json