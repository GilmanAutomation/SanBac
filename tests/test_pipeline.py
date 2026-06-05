import unittest
import tempfile
import shutil
from pathlib import Path
from sanbac.tools import load_tools
from sanbac.config import config
from sanbac.pipeline import discover_fasta_files, PipelineRunner
from sanbac.tools.base import BaseTool

class TestSanBac(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_path = Path(self.test_dir) / "input"
        self.output_path = Path(self.test_dir) / "output"
        self.input_path.mkdir()
        self.output_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_plugin_discovery(self):
        """Test that default plugins are discovered by the plugin manager."""
        tools = load_tools()
        self.assertIn("card", tools)
        self.assertIn("vfdb", tools)
        self.assertIn("prokka", tools)
        self.assertTrue(isinstance(tools["card"], BaseTool))

    def test_config(self):
        """Test configuration defaults and value setting."""
        orig_val = config.get_executable("rgi")
        config.set_executable("rgi", "custom_rgi")
        self.assertEqual(config.get_executable("rgi"), "custom_rgi")
        config.set_executable("rgi", orig_val)

    def test_fasta_discovery(self):
        """Test that discover_fasta_files correctly detects FASTA files."""
        # Create dummy files
        fasta1 = self.input_path / "sample1.fasta"
        fna1 = self.input_path / "sample2.fna"
        txt1 = self.input_path / "sample3.txt"
        
        fasta1.write_text(">seq1\nATCG\n")
        fna1.write_text(">seq2\nCGTA\n")
        txt1.write_text("not a fasta file\n")
        
        discovered = discover_fasta_files(self.input_path)
        
        self.assertEqual(len(discovered), 2)
        self.assertEqual(discovered[0].name, "sample1.fasta")
        self.assertEqual(discovered[1].name, "sample2.fna")

    def test_pipeline_runner_initialization(self):
        """Test that PipelineRunner resolves selected tools correctly."""
        runner = PipelineRunner(selected_tools=["card", "prokka"])
        self.assertEqual(len(runner.tools_to_run), 2)
        self.assertEqual(runner.tools_to_run[0].name, "card")
        self.assertEqual(runner.tools_to_run[1].name, "prokka")

        runner_default = PipelineRunner()
        names = [t.name for t in runner_default.tools_to_run]
        self.assertListEqual(names, ["card", "vfdb", "prokka"])

if __name__ == "__main__":
    unittest.main()
