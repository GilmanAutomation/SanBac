import gzip
import shutil
import subprocess
import requests
from pathlib import Path
from .base import BaseTool
from ..config import config

class VfdbTool(BaseTool):
    @property
    def name(self) -> str:
        return "vfdb"

    @property
    def description(self) -> str:
        return "VFDB (Virulence Factor Database) blastn alignment for identifying virulence factor genes"

    def is_installed(self) -> bool:
        blastn_cmd = config.get_executable("blastn")
        makeblastdb_cmd = config.get_executable("makeblastdb")
        return shutil.which(blastn_cmd) is not None and shutil.which(makeblastdb_cmd) is not None

    def update_db(self) -> bool:
        if not self.is_installed():
            print("Error: BLAST tools ('blastn' or 'makeblastdb') not found. Please install NCBI BLAST+.")
            return False

        vfdb_dir = config.db_dir / "vfdb"
        vfdb_dir.mkdir(parents=True, exist_ok=True)
        
        fasta_gz = vfdb_dir / "VFs.fasta.gz"
        fasta_file = vfdb_dir / "VFs.fasta"
        db_prefix = vfdb_dir / "vfdb_db"

        url = "http://www.mgc.ac.cn/VFs/down/VFs.fasta.gz"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        print(f"Downloading VFDB from {url}...")
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            if response.status_code == 200:
                with open(fasta_gz, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
            else:
                fallback_url = "http://www.mgc.ac.cn/VFs/down/VFs.fasta"
                print(f"Gzip file not found (HTTP {response.status_code}). Trying fallback URL: {fallback_url}...")
                res_fb = requests.get(fallback_url, headers=headers, timeout=30)
                res_fb.raise_for_status()
                with open(fasta_file, "wb") as f:
                    f.write(res_fb.content)
        except Exception as e:
            print(f"Error downloading VFDB: {e}")
            return False

        # Extract if gzipped
        if fasta_gz.exists():
            print("Extracting VFs.fasta.gz...")
            try:
                with gzip.open(fasta_gz, 'rb') as f_in:
                    with open(fasta_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                fasta_gz.unlink()
            except Exception as e:
                print(f"Error extracting database file: {e}")
                return False

        print("Building BLAST database for VFDB...")
        makeblastdb_cmd = config.get_executable("makeblastdb")
        cmd = [
            makeblastdb_cmd,
            "-in", str(fasta_file),
            "-dbtype", "nucl",
            "-out", str(db_prefix)
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("VFDB BLAST database built successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running makeblastdb: {e.stderr or e.stdout}")
            return False

    def run(self, input_file: Path, output_dir: Path, threads: int) -> Path:
        if not self.is_installed():
            raise FileNotFoundError("BLAST+ tools ('blastn' / 'makeblastdb') are not installed or not in PATH.")

        output_dir.mkdir(parents=True, exist_ok=True)
        vfdb_dir = config.db_dir / "vfdb"
        db_prefix = vfdb_dir / "vfdb_db"
        
        # Check if database files exist
        if not (db_prefix.with_suffix(".nhr").exists() or db_prefix.with_suffix(".nin").exists() or db_prefix.with_suffix(".nsq").exists()):
            print(f"VFDB database not found at {db_prefix}. Attempting download/build...")
            if not self.update_db():
                raise RuntimeError("Could not find or build VFDB database.")

        output_file = output_dir / f"{input_file.stem}_vfdb_blast.tsv"
        blastn_cmd = config.get_executable("blastn")
        
        cmd = [
            blastn_cmd,
            "-query", str(input_file),
            "-db", str(db_prefix),
            "-out", str(output_file),
            "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore",
            "-num_threads", str(threads),
            "-evalue", "1e-5",
            "-perc_identity", "80"
        ]

        print(f"[{self.name.upper()}] Running blastn against VFDB database for {input_file.name}...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"[{self.name.upper()}] Error running blastn on {input_file.name}:")
            print(e.stderr or e.stdout)
            raise e
