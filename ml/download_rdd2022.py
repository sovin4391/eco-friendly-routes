"""
Official RDD2022 Dataset Downloader and Extractor for Eco-Friendly Routes.

Downloads the official India subset (RDD2022_India.zip) and metadata directly
from the official Figshare publication:
Article: https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547
License: CC BY 4.0

Features:
- Resumable HTTP Range chunked downloads.
- Automatic retry on network interruptions with exponential backoff.
- Archive verification with zipfile testzip().
- Path traversal safe extraction preserving folder structures.
"""

import os
import sys
import time
import zipfile
import urllib.request
import urllib.error
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "dataset" / "raw" / "rdd2022"

FIGSHARE_ZIP_URL = "https://ndownloader.figshare.com/files/38030910"
LABEL_MAP_URL = "https://ndownloader.figshare.com/files/38030820"
DIR_STRUCT_URL = "https://ndownloader.figshare.com/files/38030823"

# Exact byte range of RDD2022/India.zip inside RDD2022_released_through_CRDDC2022.zip
# Determined by parsing the Zip64 central directory of the official Figshare archive:
INDIA_ZIP_START = 609341079
INDIA_ZIP_END = 1136050223
INDIA_ZIP_SIZE = INDIA_ZIP_END - INDIA_ZIP_START + 1  # 526,709,145 bytes (~502.31 MB)

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB chunks
MAX_RETRIES = 5


def download_file(url: str, dest_path: Path, description: str = "File") -> None:
    """Downloads a small file directly."""
    print(f"Downloading {description} -> {dest_path.name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())
    print(f"  Saved {dest_path.name} ({dest_path.stat().st_size} bytes)")


def download_resumable_range(
    url: str,
    dest_path: Path,
    abs_start: int,
    abs_end: int,
    total_bytes: int,
    max_retries: int = MAX_RETRIES
) -> Path:
    """
    Downloads an exact byte range from a remote URL to dest_path with resumable capability.
    """
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")
    
    current_bytes = 0
    if part_path.exists():
        current_bytes = part_path.stat().st_size
        if current_bytes > total_bytes:
            print(f"Found invalid partial file ({current_bytes} > {total_bytes}), restarting.")
            part_path.unlink()
            current_bytes = 0

    if current_bytes == total_bytes:
        print(f"Partial file already complete: {part_path.name}")
        part_path.rename(dest_path)
        return dest_path

    print(f"Starting download of {dest_path.name} ({total_bytes / (1024*1024):.2f} MB)...")
    if current_bytes > 0:
        print(f"  Resuming from byte {current_bytes} ({current_bytes / (1024*1024):.2f} MB)")

    retries = 0
    t_start = time.time()
    
    while current_bytes < total_bytes:
        chunk_start = abs_start + current_bytes
        chunk_end = min(abs_end, chunk_start + CHUNK_SIZE - 1)
        
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Range": f"bytes={chunk_start}-{chunk_end}"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if not data:
                    raise IOError("Received empty data chunk from remote server.")
                
                with open(part_path, "ab") as f:
                    f.write(data)
                
                current_bytes += len(data)
                retries = 0  # Reset on successful chunk
                
                # Progress logging
                elapsed = time.time() - t_start
                pct = (current_bytes / total_bytes) * 100
                speed = (current_bytes / (1024 * 1024)) / max(elapsed, 0.001)
                sys.stdout.write(
                    f"\r  [{pct:5.1f}%] {current_bytes / (1024*1024):6.1f} MB / {total_bytes / (1024*1024):.1f} MB "
                    f"({speed:.2f} MB/s)"
                )
                sys.stdout.flush()

        except Exception as e:
            retries += 1
            if retries > max_retries:
                print(f"\nFailed to download chunk after {max_retries} retries: {e}")
                raise
            wait_time = 2 ** retries
            print(f"\nNetwork interruption ({e}). Retrying in {wait_time}s... (attempt {retries}/{max_retries})")
            time.sleep(wait_time)

    print(f"\nDownload completed in {time.time() - t_start:.1f}s.")
    part_path.rename(dest_path)
    return dest_path


def safe_extract(zip_path: Path, extract_to: Path) -> None:
    """
    Safely extracts zip archive preventing path traversal (Zip Slip vulnerability).
    """
    print(f"Extracting {zip_path.name} to {extract_to}...")
    abs_extract_to = extract_to.resolve()
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Test archive integrity
        bad_file = zf.testzip()
        if bad_file:
            raise zipfile.BadZipFile(f"Archive corrupted at member: {bad_file}")
        
        namelist = zf.namelist()
        print(f"Archive integrity verified: {len(namelist)} entries found.")
        
        extracted_count = 0
        for member in namelist:
            target_path = (abs_extract_to / member).resolve()
            # Security: Path traversal protection
            if not str(target_path).startswith(str(abs_extract_to)):
                raise SecurityError(f"Attempted path traversal in zip member: {member}")
            
            zf.extract(member, abs_extract_to)
            extracted_count += 1
            if extracted_count % 2000 == 0 or extracted_count == len(namelist):
                sys.stdout.write(f"\r  Extracted {extracted_count}/{len(namelist)} items...")
                sys.stdout.flush()

    print(f"\nSuccessfully extracted {extracted_count} items into {extract_to}")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Download official metadata files
    label_map_file = RAW_DIR / "label_map.pbtxt"
    if not label_map_file.exists():
        download_file(LABEL_MAP_URL, label_map_file, "Official Label Map")
    
    struct_file = RAW_DIR / "Directory_Structure_CRDDC_RDD2022.txt"
    if not struct_file.exists():
        download_file(DIR_STRUCT_URL, struct_file, "Official Directory Structure")

    # 2. Download India subset archive
    india_zip = RAW_DIR / "RDD2022_India.zip"
    if india_zip.exists():
        print(f"Archive {india_zip.name} already exists ({india_zip.stat().st_size} bytes).")
        try:
            with zipfile.ZipFile(india_zip, "r") as z:
                if z.testzip() is None:
                    print("Existing archive integrity test passed.")
                else:
                    print("Existing archive corrupted. Redownloading...")
                    india_zip.unlink()
                    download_resumable_range(FIGSHARE_ZIP_URL, india_zip, INDIA_ZIP_START, INDIA_ZIP_END, INDIA_ZIP_SIZE)
        except Exception:
            print("Existing archive invalid. Redownloading...")
            india_zip.unlink()
            download_resumable_range(FIGSHARE_ZIP_URL, india_zip, INDIA_ZIP_START, INDIA_ZIP_END, INDIA_ZIP_SIZE)
    else:
        download_resumable_range(FIGSHARE_ZIP_URL, india_zip, INDIA_ZIP_START, INDIA_ZIP_END, INDIA_ZIP_SIZE)

    # 3. Extract into dataset/raw/rdd2022/
    safe_extract(india_zip, RAW_DIR)

    # 4. Verify extraction
    india_dir = RAW_DIR / "India"
    if not india_dir.exists():
        # Check if extracted without top India/ folder
        india_dir = RAW_DIR
    
    train_xmls = list((india_dir / "train" / "annotations" / "xmls").glob("*.xml")) if (india_dir / "train" / "annotations" / "xmls").exists() else []
    train_imgs = list((india_dir / "train" / "images").glob("*.jpg")) if (india_dir / "train" / "images").exists() else []
    test_imgs = list((india_dir / "test" / "images").glob("*.jpg")) if (india_dir / "test" / "images").exists() else []

    print("\nVerification of extracted files:")
    print(f"  Train XML Annotations : {len(train_xmls)}")
    print(f"  Train Camera Images   : {len(train_imgs)}")
    print(f"  Test Camera Images    : {len(test_imgs)}")
    print(f"  Total Extracted Assets: {len(train_xmls) + len(train_imgs) + len(test_imgs)}")

    if len(train_xmls) > 0 and len(train_imgs) > 0:
        print("\n[SUCCESS] RDD2022 India dataset successfully acquired and verified!")
    else:
        print("\n[WARNING] Extraction completed but expected image/annotation folders were not populated.")


if __name__ == "__main__":
    main()
