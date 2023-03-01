"""CLI to call tig from command line"""

import argparse
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
    image_gen.generate_images(granule_id=args.input_file.split('/')[-1])


if __name__ == '__main__':
    main()
