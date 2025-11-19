#!/usr/bin/env python3
"""
Reorganize existing documents to new structure
Moves files from flat directory to phi_positive/phi_negative subdirectories
and removes PHI_POS/PHI_NEG prefixes from filenames
"""
import shutil
from pathlib import Path
import json
from datetime import datetime

def reorganize_directory(source_dir: str):
    """Reorganize a directory to the new structure"""
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"❌ Directory not found: {source_dir}")
        return

    # Create new subdirectories
    phi_positive_dir = source_path / "phi_positive"
    phi_negative_dir = source_path / "phi_negative"
    metadata_dir = source_path / "metadata"

    phi_positive_dir.mkdir(exist_ok=True)
    phi_negative_dir.mkdir(exist_ok=True)
    metadata_dir.mkdir(exist_ok=True)

    # Track files for manifest
    manifest_files = []
    stats = {
        "phi_positive": 0,
        "phi_negative": 0,
        "errors": []
    }

    # Process all files in the root directory
    files = [f for f in source_path.iterdir() if f.is_file()]

    print(f"\n📂 Processing {len(files)} files from {source_dir}...")

    for file_path in files:
        filename = file_path.name

        try:
            # Determine if PHI positive or negative
            if "PHI_POS" in filename:
                # Remove PHI_POS_ prefix
                new_filename = filename.replace("PHI_POS_", "")
                new_path = phi_positive_dir / new_filename

                # Move file
                shutil.move(str(file_path), str(new_path))

                manifest_files.append({
                    "file_path": f"phi_positive/{new_filename}",
                    "phi_status": "positive",
                    "original_name": filename
                })
                stats["phi_positive"] += 1
                print(f"  ✓ {filename} → phi_positive/{new_filename}")

            elif "PHI_NEG" in filename:
                # Remove PHI_NEG_ prefix
                new_filename = filename.replace("PHI_NEG_", "")
                new_path = phi_negative_dir / new_filename

                # Move file
                shutil.move(str(file_path), str(new_path))

                manifest_files.append({
                    "file_path": f"phi_negative/{new_filename}",
                    "phi_status": "negative",
                    "original_name": filename
                })
                stats["phi_negative"] += 1
                print(f"  ✓ {filename} → phi_negative/{new_filename}")
            else:
                # Not a generated PHI file, skip
                pass

        except Exception as e:
            error_msg = f"Error processing {filename}: {e}"
            stats["errors"].append(error_msg)
            print(f"  ❌ {error_msg}")

    # Create manifest
    manifest_path = metadata_dir / "manifest.json"
    manifest_data = {
        "reorganized_at": datetime.now().isoformat(),
        "source_directory": str(source_dir),
        "total_files": len(manifest_files),
        "phi_positive": stats["phi_positive"],
        "phi_negative": stats["phi_negative"],
        "files": manifest_files
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"\n📊 Summary:")
    print(f"  • PHI Positive: {stats['phi_positive']} files")
    print(f"  • PHI Negative: {stats['phi_negative']} files")
    print(f"  • Errors: {len(stats['errors'])}")
    print(f"  • Manifest: {manifest_path}")
    print(f"\n✅ Reorganization complete!\n")

    return stats

if __name__ == "__main__":
    # Reorganize production_batch_1000
    reorganize_directory("output/production_batch_1000")
