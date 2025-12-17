"""CLI to call tig from command line"""

import argparse
import logging
from podaac.tig import tig


def main() -> None:
    """
    Main entry point for the application.

    Returns
    -------

    """
    parser = argparse.ArgumentParser(
        description='Config variables subsitatution utility')
    parser.add_argument('--input_file', type=str, required=True,
                        help='')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='')
    parser.add_argument('--config_file', type=str, required=True,
                        help='')
    parser.add_argument('--palette_dir', type=str, required=True,
                        help='')

    args = parser.parse_args()

    image_gen = tig.TIG(args.input_file, args.output_dir, args.config_file, args.palette_dir)
    try:
        image_gen.generate_images(granule_id=args.input_file.split('/')[-1])
    except Exception as ex:
        logging.error(
            "Error in generate_images: %s. Inputs: input_file=%s, output_dir=%s, config_file=%s, palette_dir=%s",
            ex, args.input_file, args.output_dir, args.config_file, args.palette_dir
        )
        raise


if __name__ == '__main__':
    main()
