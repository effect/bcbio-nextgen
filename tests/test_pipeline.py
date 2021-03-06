"""Test individual components of the analysis pipeline.
"""
import os
import shutil
import unittest

from nose.plugins.attrib import attr

from bcbio.distributed.messaging import parallel_runner
from bcbio.pipeline.config_utils import load_config
from bcbio.pipeline.run_info import get_run_info
from bcbio.provenance import programs
from bcbio.variation import vcfutils

class RunInfoTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")

    @attr(speed=1)
    def test_run_info_combine(self):
        """Combine multiple lanes in a test run into a single combined lane.
        """
        run_info_yaml = os.path.join(self.data_dir, "run_info-alternatives.yaml")
        _, _, run_info = get_run_info("", {}, run_info_yaml)
        assert len(run_info["details"]) == 2
        assert len(run_info["details"][0]) == 3
        x1, x2, x3 = run_info["details"][0]
        assert x1["description"] == "1: BC1"
        assert x2["description"] == "1: BC2"
        assert x3["genome_build"] == "mm9"
        x1 = run_info["details"][1][0]
        assert x1["barcode_id"] is None

    @attr(speed=1)
    def test_programs(self):
        """Identify programs and versions used in analysis.
        """
        config = load_config(os.path.join(self.data_dir, "automated",
                                          "post_process-sample.yaml"))
        print programs.get_versions(config)

class VCFUtilTest(unittest.TestCase):
    """Test various utilities for dealing with VCF files.
    """
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")

    @attr(speed=1)
    def test_1_parallel_vcf_combine(self):
        """Parallel combination of VCF files, split by chromosome.
        """
        var_dir = os.path.join(self.data_dir, "variants")
        files = [os.path.join(var_dir, "S1-variants.vcf"), os.path.join(var_dir, "S2-variants.vcf")]
        out_file = os.path.join(var_dir, "S1_S2-combined.vcf")
        ref_file = os.path.join(self.data_dir, "genomes", "hg19", "seq", "hg19.fa")
        config = load_config(os.path.join(self.data_dir, "automated",
                                          "post_process-sample.yaml"))
        run_parallel = parallel_runner({"type": "local", "cores": 1}, {}, config)
        region_dir = os.path.join(var_dir, "S1_S2-combined-regions")
        if os.path.exists(region_dir):
            shutil.rmtree(region_dir)
        if os.path.exists(out_file):
            os.remove(out_file)
        vcfutils.parallel_combine_variants(files, out_file, ref_file, config, run_parallel)

    @attr(speed=1)
    def test_2_vcf_exclusion(self):
        """Exclude samples from VCF files.
        """
        fname = os.path.join(self.data_dir, "variants", "S1_S2-combined.vcf")
        ref_file = os.path.join(self.data_dir, "genomes", "hg19", "seq", "hg19.fa")
        config = load_config(os.path.join(self.data_dir, "automated",
                                          "post_process-sample.yaml"))
        out_file = "%s-exclude%s" % os.path.splitext(fname)
        to_exclude = ["S1"]
        if os.path.exists(out_file):
            os.remove(out_file)
        vcfutils.exclude_samples(fname, out_file, to_exclude, ref_file, config)
