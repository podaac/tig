"""
==============
test_tig.py
==============

Test TIG functionality.
"""
import filecmp
import os
import shutil
import unittest
from podaac.tig import tig


class TestTIG(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.input_dir = f'{self.test_dir}/input'
        self.output_dir = f'{self.test_dir}/output'
        self.config_dir = f'{self.test_dir}/configs'
        self.palette_dir = f'{self.test_dir}/palettes'
        self.image_dir = f'{self.test_dir}/images'

        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    @classmethod
    def tearDownClass(self):
        # Remove output directory and files
        shutil.rmtree(self.output_dir)

    def test_image_generation_default(self):
        config_file = f'{self.config_dir}/PODAAC-CYGNS-C2H10.cfg'
        input_file = f'{self.input_dir}/cyg.ddmi.s20201031-000000-e20201031-235959.l2.surface-flux-cdr.a10.d10.nc'
        output_dir = f'{self.output_dir}/cyg.ddmi.s20201031-000000-e20201031-235959.l2.surface-flux-cdr.a10.d10.nc'
        image_dir = f'{self.image_dir}/cyg.ddmi.s20201031-000000-e20201031-235959.l2.surface-flux-cdr.a10.d10.nc'

        image_gen = tig.TIG(input_file, output_dir, config_file, self.palette_dir)
        image_gen.generate_images()

        for filename in os.listdir(output_dir):
            output_file = f'{output_dir}/{filename}'
            image_file = f'{image_dir}/{filename}'
            self.assertTrue(filecmp.cmp(output_file, image_file), "Output image does not match expected")

    def test_image_generation_with_nested_groups(self):
        config_file = f'{self.config_dir}/SWOT_SIMULATED_L2_NADIR_SSH_ECCO_LLC4320_CALVAL_V1_no_leading_slash.cfg'
        input_file = f'{self.input_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'
        output_dir = f'{self.output_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'
        image_dir = f'{self.image_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'

        image_gen = tig.TIG(input_file, output_dir, config_file, self.palette_dir)
        image_gen.generate_images()

        for filename in os.listdir(output_dir):
            output_file = f'{output_dir}/{filename}'
            image_file = f'{image_dir}/{filename}'
            self.assertTrue(filecmp.cmp(output_file, image_file), "Output image does not match expected")

    def test_image_generation_with_nested_groups_leading_slash(self):
        config_file = f'{self.config_dir}/SWOT_SIMULATED_L2_NADIR_SSH_ECCO_LLC4320_CALVAL_V1_leading_slash.cfg'
        input_file = f'{self.input_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'
        output_dir = f'{self.output_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'
        image_dir = f'{self.image_dir}/SWOT_GPR_2PTP003_005_20111115_030538_20111115_035643.nc'

        image_gen = tig.TIG(input_file, output_dir, config_file, self.palette_dir)
        image_gen.generate_images()

        for filename in os.listdir(output_dir):
            output_file = f'{output_dir}/{filename}'
            image_file = f'{image_dir}/{filename}'
            self.assertTrue(filecmp.cmp(output_file, image_file), "Output image does not match expected")


if __name__ == '__main__':
    unittest.main()
