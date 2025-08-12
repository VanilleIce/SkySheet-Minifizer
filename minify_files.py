# Copyright (C) 2025 VanilleIce

import json
import os
import shutil
import sys
import re

def detect_encoding(file_path):
    """
    Automatically detects file encoding by testing common encodings.
    
    Args:
        file_path: Path to the file to test
        
    Returns:
        str: Detected encoding ('utf-8' or 'utf-16-le')
        Defaults to 'utf-8' if none match
    """
    encodings = ['utf-8', 'utf-16-le']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    
    # Fallback to UTF-8 with warning
    print(f"[WARNING] Encoding detection failed for {file_path}, using UTF-8")
    return 'utf-8'

def read_file(file_path, encoding):
    """
    Reads file content using specified encoding.
    
    Args:
        file_path: Path to input file
        encoding: Encoding to use for reading
        
    Returns:
        str: File content as string
    """
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()

def write_file(file_path, content, encoding):
    """
    Writes content to file using original encoding.
    
    Args:
        file_path: Output file path
        content: Content to write
        encoding: Original encoding to preserve
    """
    with open(file_path, 'w', encoding=encoding) as file:
        file.write(content)

def minify_json(content):
    """
    Minifies JSON content while preserving spaces within string values.
    
    Args:
        content: JSON string to minify
        
    Returns:
        str: Minified JSON or None if invalid JSON
    """
    try:
        # Parse and re-serialize with minimal formatting
        json_data = json.loads(content)
        return json.dumps(json_data, separators=(',', ':'))
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] Invalid JSON structure: {e}")
        return None

def minify_text(content):
    """
    Minifies plain text content by removing unnecessary whitespace.
    
    Args:
        content: Text content to minify
        
    Returns:
        str: Minified text content
    """
    # Remove all newlines and tabs
    content = re.sub(r'[\r\n\t]+', ' ', content)
    # Collapse multiple spaces into one
    content = re.sub(r' {2,}', ' ', content)
    # Remove spaces around JSON punctuation
    content = re.sub(r'\s*([\{\}\[\]:,])\s*', r'\1', content)
    # Remove leading/trailing whitespace
    return content.strip()

def process_file(file_path):
    """
    Processes individual files:
    1. Creates backup
    2. Minifies content while preserving JSON string spaces
    3. Saves with original encoding and .skysheet extension
    
    Args:
        file_path: Path to input file
        
    Returns:
        bool: True if successful, False if error
    """
    try:
        # Validate file existence
        if not os.path.isfile(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return False
        
        # Detect original encoding
        original_encoding = detect_encoding(file_path)
        
        # Prepare backup system
        original_dir = os.path.dirname(file_path)
        backup_folder = os.path.join(original_dir, "backup")
        os.makedirs(backup_folder, exist_ok=True)
        
        # Create backup
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_folder, f"{filename}.bak")
        shutil.copy2(file_path, backup_path)
        
        # Read content with original encoding
        content = read_file(file_path, original_encoding)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Process based on file type
        if file_ext == '.json':
            minified_content = minify_json(content)
        else:  # .txt or .skysheet
            minified_content = minify_text(content)
        
        if minified_content is None:
            return False
        
        # Create output file
        new_filename = os.path.splitext(filename)[0] + ".skysheet"
        new_file_path = os.path.join(original_dir, new_filename)
        write_file(new_file_path, minified_content, original_encoding)
        
        # Report success
        print(f"[SUCCESS] Minified: {filename} → {new_filename}")
        print(f"          Encoding: {original_encoding.upper()}")
        print(f"          Backup: {backup_path}")
        return True
        
    except Exception as e:
        # Detailed error reporting
        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.basename(file_path)
        print(f"[CRITICAL ERROR] Processing {filename}")
        print(f"  • Error Type: {type(e).__name__}")
        print(f"  • Line: {exc_tb.tb_lineno}")
        print(f"  • Details: {str(e)}")
        return False

def process_directory(directory):
    """
    Recursively processes all supported files in a directory.
    
    Args:
        directory: Root directory to process
        
    Returns:
        tuple: (success_count, error_count)
    """
    supported_extensions = ('.json', '.txt', '.skysheet')
    count = 0
    errors = 0
    
    print(f"\nProcessing directory: {directory}")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_extensions):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    count += 1
                else:
                    errors += 1
                    
    return count, errors

if __name__ == "__main__":
    # Command line interface
    if len(sys.argv) < 2:
        print("SkySheet File Minifier")
        print("Usage: Drag files/folders onto mini.bat")
        print("Supported formats: JSON, TXT, SkySheet")
        sys.exit(1)

    # Processing statistics
    total_count = 0
    total_errors = 0
    processed_paths = []

    print("Starting SkySheet minification...")
    
    for path in sys.argv[1:]:
        # Normalize path and check existence
        path = os.path.normpath(path)
        if not os.path.exists(path):
            print(f"\n[WARNING] Path does not exist: {path}")
            total_errors += 1
            continue
            
        processed_paths.append(path)
        
        # Process based on type
        if os.path.isfile(path):
            print(f"\nProcessing file: {os.path.basename(path)}")
            if process_file(path):
                total_count += 1
            else:
                total_errors += 1
                
        elif os.path.isdir(path):
            count, errors = process_directory(path)
            total_count += count
            total_errors += errors
            
        else:
            print(f"\n[ERROR] Unsupported path type: {path}")
            total_errors += 1

    # Final report
    print("\n" + "="*50)
    print("MINIFICATION SUMMARY")
    print("="*50)
    print(f"Processed locations: {', '.join(processed_paths)}")
    print(f"• Successfully minified: {total_count} files")
    print(f"• Errors encountered: {total_errors}")
    print(f"• Backups stored in 'backup' subdirectories")
    print("\nImportant Notes:")
    print("- Original files remain unchanged in backup folders")
    print("- Output files preserve original encoding (UTF-8 or UTF-16-LE)")
    print("- JSON files are minified while preserving spaces in strings")
    print("- Text files have all unnecessary whitespace removed")
    print("- Output files have .skysheet extension")
    print("\nMinification complete!")