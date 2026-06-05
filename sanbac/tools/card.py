import shutil
import subprocess
from pathlib import Path
from .base import BaseTool
from ..config import config

class CardTool(BaseTool):
    @property
    def name(self) -> str:
        return "card"

    @property
    def description(self) -> str:
        return "CARD (Comprehensive Antibiotic Resistance Database) via RGI (Resistance Gene Identifier) for Antibiotic Resistance Genes (ARGs)"

    def is_installed(self) -> bool:
        rgi_cmd = config.get_executable("rgi")
        return shutil.which(rgi_cmd) is not None

    def update_db(self) -> bool:
        rgi_cmd = config.get_executable("rgi")
        if not self.is_installed():
            print("Error: 'rgi' command not found. Please install RGI first.")
            return False
        
        print("Updating CARD database using RGI...")
        try:
            result = subprocess.run(
                [rgi_cmd, "database", "--download"],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error updating CARD database: {e.stderr or e.stdout}")
            return False

    def run(self, input_file: Path, output_dir: Path, threads: int) -> Path:
        rgi_cmd = config.get_executable("rgi")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # RGI appends extensions to output prefix automatically (e.g. .txt, .json).
        output_prefix = output_dir / input_file.stem
        
        cmd = [
            rgi_cmd,
            "main",
            "--input_sequence", str(input_file),
            "--output_file", str(output_prefix),
            "--input_type", "contig",
            "-n", str(threads),
            "--clean"
        ]
        
        print(f"[{self.name.upper()}] Analyzing {input_file.name} with {threads} thread(s)...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            txt_output = Path(f"{output_prefix}.txt")
            if txt_output.exists():
                return txt_output
            return output_dir
        except subprocess.CalledProcessError as e:
            print(f"[{self.name.upper()}] Error running CARD/RGI on {input_file.name}:")
            print(e.stderr or e.stdout)
            raise e
