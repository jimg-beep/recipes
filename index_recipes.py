#!/usr/bin/env python3
"""
Recipe Indexer - Extracts text from PDFs, HTML, and text files to create a searchable index
Copies original files for viewing
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict

def extract_pdf_text(filepath: Path) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return '\n'.join(text)
    except ImportError:
        print("PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        return ""

def extract_html_text(filepath: Path) -> str:
    """Extract text from HTML file"""
    try:
        from bs4 import BeautifulSoup
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator=' ', strip=True)
    except ImportError:
        print("BeautifulSoup not installed. Install with: pip install beautifulsoup4")
        return ""
    except Exception as e:
        print(f"Error reading HTML {filepath}: {e}")
        return ""

def extract_text_file(filepath: Path) -> str:
    """Extract text from plain text file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file {filepath}: {e}")
        return ""

def create_preview(text: str, max_length: int = 200) -> str:
    """Create a preview snippet from text"""
    # Remove extra whitespace
    import re
    cleaned = re.sub(r'\s+', ' ', text).strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rsplit(' ', 1)[0] + '...'

def index_recipes(recipes_dir: str, output_dir: str = '.', output_file: str = 'recipes_index.json'):
    """
    Index all recipe files in the given directory
    
    Args:
        recipes_dir: Path to directory containing recipe files
        output_dir: Directory where index and recipe copies will be saved
        output_file: Filename for output JSON index file
    """
    recipes_path = Path(recipes_dir)
    output_path = Path(output_dir)
    
    if not recipes_path.exists():
        print(f"Error: Directory {recipes_dir} does not exist")
        return
    
    # Create recipes subdirectory for file copies
    recipes_copy_dir = output_path / 'recipes'
    recipes_copy_dir.mkdir(exist_ok=True)
    
    recipes = []
    
    # Supported file extensions
    pdf_ext = ['.pdf']
    html_ext = ['.html', '.htm']
    text_ext = ['.txt', '.md']
    
    all_files = list(recipes_path.rglob('*'))
    recipe_files = [f for f in all_files if f.is_file() and f.suffix.lower() in pdf_ext + html_ext + text_ext]
    
    print(f"Found {len(recipe_files)} recipe files")
    
    for idx, filepath in enumerate(recipe_files, 1):
        print(f"Processing {idx}/{len(recipe_files)}: {filepath.name}")
        
        ext = filepath.suffix.lower()
        
        # Extract text based on file type
        if ext in pdf_ext:
            text = extract_pdf_text(filepath)
            file_type = 'pdf'
        elif ext in html_ext:
            text = extract_html_text(filepath)
            file_type = 'html'
        else:
            text = extract_text_file(filepath)
            file_type = 'text'
        
        if not text:
            print(f"  Warning: No text extracted from {filepath.name}")
            text = ""  # Continue anyway, we'll still have the file to view
        
        # Copy original file to recipes directory
        # Use a safe filename (replace spaces, special chars)
        safe_filename = f"{idx:03d}_{filepath.name}"
        safe_filename = safe_filename.replace(' ', '_')
        dest_path = recipes_copy_dir / safe_filename
        
        try:
            shutil.copy2(filepath, dest_path)
            web_path = f"recipes/{safe_filename}"
        except Exception as e:
            print(f"  Error copying file: {e}")
            continue
        
        recipe = {
            'id': idx,
            'filename': filepath.name,
            'file_path': web_path,  # Path for web to access
            'type': file_type,
            'content': text,  # Full text for searching
            'preview': create_preview(text),
            'size': filepath.stat().st_size
        }
        
        recipes.append(recipe)
    
    # Write index to JSON file
    index_path = output_path / output_file
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Successfully indexed {len(recipes)} recipes")
    print(f"✓ Index saved to: {index_path.absolute()}")
    print(f"✓ Recipe files copied to: {recipes_copy_dir.absolute()}")
    print(f"✓ Index size: {index_path.stat().st_size / 1024:.1f} KB")
    print(f"✓ Total recipe files size: {sum(r['size'] for r in recipes) / 1024 / 1024:.1f} MB")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python index_recipes.py <recipes_directory> [output_directory] [output_file]")
        print("\nExample: python index_recipes.py ./my_recipes ./recipe-site recipes_index.json")
        print("\nThis will create:")
        print("  - recipes_index.json (search index)")
        print("  - recipes/ folder (copies of original files)")
        sys.exit(1)
    
    recipes_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'recipes_index.json'
    
    print("Recipe Indexer")
    print("=" * 50)
    print(f"Source directory: {recipes_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Index file: {output_file}")
    print("=" * 50)
    print()
    
    index_recipes(recipes_dir, output_dir, output_file)
