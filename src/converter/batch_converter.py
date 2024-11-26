import logging
import sys
from collections import namedtuple
from pathlib import Path

import configargparse as argparse

from .pytorch_converter import PyTorchConverter

FilePair = namedtuple("FilePair", ["input_file", "output_file"])


def setup_logging(log_filename: str) -> None:
    """Set up logging to file and stream handlers."""
    formatter = logging.Formatter("%(levelname)s [%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
    handlers = []
    level: int = logging.INFO

    if log_filename:
        file_handler = logging.FileHandler(log_filename, mode="w")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
        level = logging.DEBUG

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    logging.basicConfig(level=level, handlers=handlers)


def convert_pytorch(input_file: str, output_file: str, simulate: bool) -> None:
    """Convert PyTorch input trace to Chakra execution trace."""
    converter = PyTorchConverter()
    converter.convert(input_file, output_file, simulate)


def find_linked_traces(
    input_dir: str, output_dir: str, linked_trace_identifier: str, compression: bool
) -> dict[str, FilePair]:
    input_path = Path(input_dir)
    result: dict[str, tuple[str, str]] = {}
    file_extension = ".et.gz" if compression else ".et"
    for item in sorted(input_path.iterdir()):
        if item.is_dir():
            continue
        if item.name == linked_trace_identifier:
            raise ValueError(
                "Identifier for linked traces must not be equal to filename: file_name: "
                "'{item.name}', linked_trace_identifer: '{linked_trace_identifier}'"
            )
        if linked_trace_identifier in item.name:
            trace_name = item.name.split(linked_trace_identifier)[0]
            result[trace_name] = FilePair(
                input_file=item.as_posix(),
                output_file=Path(output_dir, trace_name + file_extension).as_posix(),
            )
    return result


def convert_pytorch_batch(args: argparse.Namespace) -> None:
    trace_pairs = find_linked_traces(
        input_dir=args.input_directory,
        output_dir=args.output_directory,
        linked_trace_identifier=args.linked_trace_identifier,
        compression=args.compress,
    )
    if not trace_pairs:
        logging.error(
            "No traces with identifier '%s' found in directory '%s'!",
            args.linked_trace_identifier,
            args.input_directory,
        )
        sys.exit(-1)
    Path(args.output_directory).mkdir(exist_ok=True, parents=True)
    for idx, (trace_name, file_pair) in enumerate(trace_pairs.items()):
        logging.info(
            "Converting file %d of %d: trace_name: '%s', input: '%s', output: '%s'",
            idx + 1,
            len(trace_pairs),
            trace_name,
            file_pair.input_file,
            file_pair.output_file,
        )
        convert_pytorch(input_file=file_pair.input_file, output_file=file_pair.output_file, simulate=False)


def main() -> None:
    """Convert to Chakra execution trace in the protobuf format."""
    parser = argparse.ArgumentParser(
        description=(
            "Chakra execution trace converter for simulators. This converter is designed for any downstream "
            "simulators that take Chakra execution traces in the protobuf format. This converter takes an input "
            "file directory in another format and generates Chakra execution trace outputs in the protobuf format."
        )
    )

    parser.add_argument("--log-filename", type=str, default="", help="Debug Log filename")

    parser.add_argument(
        "--input-directory",
        type=str,
        env_var="INPUT_DIRECTORY",
        required=True,
        help="Input directory with Chakra host + device traces in the JSON format",
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        env_var="OUTPUT_DIRECTORY",
        required=True,
        help="Output directory with Chakra host + device traces in the protobuf format",
    )
    parser.add_argument(
        "--linked-trace-identifier",
        type=str,
        default="_linked.json",
        required=False,
        help="String fragment to identify linked chakra traces (default='_linked.trace.json')",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        required=False,
        help="Whether or not to use compression for the linked traces",
    )

    args = parser.parse_args()
    setup_logging(log_filename=args.log_filename)
    convert_pytorch_batch(args)
    logging.info(f"Conversion successful. Output files are available at '{args.output_directory}'")


if __name__ == "__main__":
    main()
