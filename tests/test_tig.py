"""
==============
test_tig.py
==============

Test TIG functionality.
"""
import logging
import os
import shutil
import unittest
from typing import Union, Tuple, Optional

import cv2
import filecmp
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

from podaac.tig import tig

def images_are_similar(
    image1: Union[str, np.ndarray], 
    image2: Union[str, np.ndarray], 
    threshold: float = 0.95,
    resize_to: Optional[Tuple[int, int]] = None,
) -> Tuple[bool, float]:
    """
    Compare two images using Structural Similarity Index (SSIM) and optional preprocessing.
    
    Args:
        image1: Path to first image or numpy array
        image2: Path to second image or numpy array
        threshold: Similarity threshold (0 to 1), higher means more similar
        resize_to: Optional tuple of (width, height) to resize images before comparison
        
    Returns:
        Tuple of (bool indicating if images are similar, float similarity score)
        
    Raises:
        ValueError: If images cannot be opened or processed
        TypeError: If input types are invalid
    """
    try:
        # Convert inputs to numpy arrays if they're file paths
        if isinstance(image1, str):
            array_image1 = np.array(Image.open(image1).convert('L'))
        elif isinstance(image1, np.ndarray):
            array_image1 = image1 if len(image1.shape) == 2 else cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        else:
            raise TypeError("image1 must be a file path or numpy array")
            
        if isinstance(image2, str):
            array_image2 = np.array(Image.open(image2).convert('L'))
        elif isinstance(image2, np.ndarray):
            array_image2 = image2 if len(image2.shape) == 2 else cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        else:
            raise TypeError("image2 must be a file path or numpy array")

        # Resize images if specified
        if resize_to:
            array_image1 = cv2.resize(array_image1, resize_to, interpolation=cv2.INTER_AREA)
            array_image2 = cv2.resize(array_image2, resize_to, interpolation=cv2.INTER_AREA)
        
        # Ensure images are same size
        if array_image1.shape != array_image2.shape:
            raise ValueError(
                f"Images must be same size. Got {array_image1.shape} and {array_image2.shape}"
            )

        # Apply basic preprocessing
        array_image1 = cv2.equalizeHist(array_image1)  # Normalize contrast
        array_image2 = cv2.equalizeHist(array_image2)
        
        # Compute SSIM
        similarity_score = ssim(array_image1, array_image2)
        
        return similarity_score >= threshold, similarity_score

    except Exception as e:
        logging.error(f"Error comparing images: {str(e)}")
        raise

def get_image_differences(
    image1: Union[str, np.ndarray],
    image2: Union[str, np.ndarray],
    threshold: float = 1.0
) -> Optional[np.ndarray]:
    """
    Generate a difference mask highlighting areas where images differ.
    
    Args:
        image1: Path to first image or numpy array
        image2: Path to second image or numpy array
        threshold: Similarity threshold for considering pixels different
        
    Returns:
        Numpy array containing the difference mask, or None if error occurs
    """
    try:
        # Convert images to arrays using the main function's logic
        if isinstance(image1, str):
            array_image1 = np.array(Image.open(image1).convert('L'))
        else:
            array_image1 = image1 if len(image1.shape) == 2 else cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            
        if isinstance(image2, str):
            array_image2 = np.array(Image.open(image2).convert('L'))
        else:
            array_image2 = image2 if len(image2.shape) == 2 else cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Compute absolute difference
        diff = cv2.absdiff(array_image1, array_image2)
        
        # Threshold to create binary mask of significant differences
        _, mask = cv2.threshold(diff, int(255 * (1 - threshold)), 255, cv2.THRESH_BINARY)
        
        return mask
        
    except Exception as e:
        logging.error(f"Error generating difference mask: {str(e)}")
        return None

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
            self.assertTrue(images_are_similar(output_file, image_file), f"{output_file} and {image_file} are not similar")

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
            self.assertTrue(images_are_similar(output_file, image_file), f"{output_file} and {image_file} are not similar")

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
            self.assertTrue(images_are_similar(output_file, image_file), f"{output_file} and {image_file} are not similar")

if __name__ == '__main__':
    unittest.main()
