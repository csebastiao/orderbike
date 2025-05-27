"""
Relabel every selected file to have a padding within the number trial.
"""

from pathlib import Path

if __name__ == "__main__":
    PADDING = 3
    folderoot = "./data/processed/ignored_files/paper/grid/"
    p = Path(folderoot).glob("**/*")
    files = [x for x in p if x.is_file()]
    filtered_list = [x for x in files if "connected" in str(x)]
    for f in filtered_list:
        split = f.stem.split("_")
        ext = f.suffix
        updated_name = "_".join(split[:-1]) + "_" + split[-1].zfill(PADDING)
        f.rename(Path(f.parent, updated_name + ext))
