
# SkySheet File Minifier

This script processes JSON, TXT, and SkySheet files by:
1. Creating backups in a "backup" subdirectory
2. Minifying all content while preserving spaces within JSON strings
3. Preserving original file encoding (UTF-8 or UTF-16-LE)
4. Renaming output files with the .skysheet extension

Key Features:
- Preserves original file encoding (UTF-8 or UTF-16-LE)
- Maintains spaces within JSON string values
- Removes all other unnecessary whitespace
- Recursive directory processing
- Detailed error reporting with line numbers
- Backup preservation with .bak extension

Usage:
1. Drag files/folders onto mini.bat
2. Processed files appear as FILENAME.skysheet
3. Originals preserved in "backup" folders
