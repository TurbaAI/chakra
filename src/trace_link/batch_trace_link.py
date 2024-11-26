import logging
import os
import sys
from collections import namedtuple
from pathlib import Path

import configargparse as argparse

from ..converter.pytorch_converter import PyTorchConverter
from .trace_linker import TraceLinker

ToolArgs = namedtuple(
    "ToolArgs",
    [
        "trace_name",
        "host_trace_file_path",
        "device_trace_file_path",
        "linked_trace_file_path",
        "converted_trace_file_path",
    ],
)

LINKED_TRACE_EXT = "_linked.json"
LINKED_TRACE_EXT_COMPRESSED = "_linked.json.gz"
CONVERTED_TRACE_EXT = ".et"
CONVERTED_TRACE_EXT_COMPRESSED = ".et.gz"


def setup_logging(log_filename: str) -> None:
    """Set up logging to file and stream handlers."""
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", datefmt="%m/%d/%Y %H:%M:%S")
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

    logging.basicConfig(level=level, handlers=handlers, force=True)


def find_tool_args(
    input_directory: str,
    output_directory: str,
    host_trace_identifier: str,
    device_trace_identifier: str,
    compress: bool,
) -> list[ToolArgs]:
    input_path = Path(input_directory)
    linked_trace_extension = LINKED_TRACE_EXT_COMPRESSED if compress else LINKED_TRACE_EXT
    converted_trace_extension = CONVERTED_TRACE_EXT_COMPRESSED if compress else CONVERTED_TRACE_EXT
    tool_args: list[ToolArgs] = []
    host_trace_paths: list[Path] = []
    device_trace_paths: list[Path] = []
    for item in sorted(input_path.iterdir()):
        if item.is_dir():
            continue
        if host_trace_identifier in item.name:
            host_trace_paths.append(item)
        elif device_trace_identifier in item.name:
            device_trace_paths.append(item)
    for host_trace_path in sorted(host_trace_paths):
        found_device_trace_path: Path = Path()
        for i in range(1, len(host_trace_path.name)):
            candidate_device_trace_paths = [
                trace_path for trace_path in device_trace_paths if host_trace_path.name[0:i] in trace_path.name
            ]
            if len(candidate_device_trace_paths) == 1:
                found_device_trace_path = candidate_device_trace_paths[0]
                break
        if not found_device_trace_path:
            logging.error(f"Could not find matching device trace for host trace '{host_trace_path.name}'!")
        else:
            trace_name = os.path.commonprefix([host_trace_path.name, found_device_trace_path.name])
            tool_args.append(
                ToolArgs(
                    trace_name=trace_name,
                    host_trace_file_path=host_trace_path,
                    device_trace_file_path=found_device_trace_path,
                    linked_trace_file_path=Path(output_directory, trace_name + linked_trace_extension),
                    converted_trace_file_path=Path(output_directory, trace_name + converted_trace_extension),
                )
            )
    return tool_args


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "This tool links Chakra host execution traces with Chakra device traces. Chakra host execution "
            "traces include host-side (CPU) operators only, missing GPU operators. While these traces show "
            "dependencies between operators, they lack operator duration. Chakra device traces include "
            "device-side (GPU) operators in an unstructured timeline without explicit dependencies. This tool "
            "adds duration information to CPU operators in Chakra host traces and encodes GPU operators into the "
            "final Chakra host + device trace in JSON format. The trace linker also identifies key dependencies, "
            "such as inter-thread and synchronization dependencies. For more information, see the guide at https://"
            "github.com/mlcommons/chakra/wiki/Chakra-Execution-Trace-Collection-%E2%80%90-A-Comprehensive-Guide-on-"
            "Merging-PyTorch-and-Kineto-Traces"
        )
    )
    parser.add_argument(
        "--input-directory",
        type=str,
        env_var="INPUT_DIRECTORY",
        required=True,
        help="Directory containing Chakra host and device trace files",
    )
    parser.add_argument(
        "--chakra-host-trace-identifier",
        type=str,
        required=False,
        default=".et.trace.json",
        help=(
            "String fragment used to identify a chakra host trace. Can be a part of the filename or an extension. "
            "Note that the linked output trace will be constructed from the substrings common to host and device trace "
            "BEFORE the identifier! So if your traces are named, e.g. 'test_a.host.trace.json.gz' and "
            "'test_a.device.trace.json.gz'  and your identifiers are '.host.trace.json.gz' and '.device.trace.json.gz' "
            "the resulting file will be named 'test_a_linked.json.gz'"
        ),
    )
    parser.add_argument(
        "--chakra-device-trace-identifier",
        type=str,
        required=False,
        default=".pt.trace.json",
        help=(
            "String fragment used to identify a chakra device trace. Can be a part of the filename or an extension. "
            "Note that the linked output trace will be constructed from the substrings common to host and device trace "
            "BEFORE the identifier! So if your traces are named, e.g. 'test_a.host.trace.json.gz' and "
            "'test_a.device.trace.json.gz'  and your identifiers are '.host.trace.json.gz' and '.device.trace.json.gz' "
            "the resulting file will be named 'test_a_linked.json.gz'"
        ),
    )
    parser.add_argument(
        "--output-directory",
        env_var="OUTPUT_DIRECTORY",
        type=str,
        required=True,
        help="Path for the output Chakra host + device traces in the JSON format",
    )

    parser.add_argument(
        "--compress",
        default=False,
        action="store_true",
        required=False,
        help="Whether or not to use compression for the linked traces",
    )
    parser.add_argument(
        "--convert",
        default=False,
        action="store_true",
        required=False,
        help="Whether or not to convert the linked traces equivalent to using chakra_converter",
    )
    parser.add_argument("--log-filename", type=str, default="", help="Debug Log filename")

    args = parser.parse_args()

    setup_logging(args.log_filename)
    logging.info(args)
    tool_args: list[ToolArgs] = find_tool_args(
        input_directory=args.input_directory,
        output_directory=args.output_directory,
        host_trace_identifier=args.chakra_host_trace_identifier,
        device_trace_identifier=args.chakra_device_trace_identifier,
        compress=args.compress,
    )
    if not tool_args:
        logging.error(
            "No trace pairs found (input_dir: '%s', host_trace_identifier: '%s', device_trace_identifier: '%s')",
            args.input_directory,
            args.chakra_host_trace_identifier,
            args.device_trace_identifier,
        )
        sys.exit(-1)

    Path(args.output_directory).mkdir(exist_ok=True, parents=True)
    for idx, tool_arg in enumerate(tool_args):
        logging.info(
            "Linking file pair %d of %d: inputs: ('%s', '%s'), output: '%s'",
            idx + 1,
            len(tool_args),
            tool_arg.host_trace_file_path.as_posix(),
            tool_arg.device_trace_file_path.as_posix(),
            tool_arg.linked_trace_file_path.as_posix(),
        )
        linker = TraceLinker()
        linker.link(
            rank=idx,
            chakra_host_trace=tool_arg.host_trace_file_path.as_posix(),
            chakra_device_trace=tool_arg.device_trace_file_path.as_posix(),
            output_file=tool_arg.linked_trace_file_path.as_posix(),
        )

    if args.convert:
        for idx, tool_arg in enumerate(tool_args):
            logging.info(
                "Converting linked trace %d of %d: input: '%s', output: '%s'",
                idx + 1,
                len(tool_args),
                tool_arg.linked_trace_file_path.as_posix(),
                tool_arg.converted_trace_file_path.as_posix(),
            )
            converter = PyTorchConverter()
            converter.convert(
                tool_arg.linked_trace_file_path.as_posix(),
                tool_arg.converted_trace_file_path.as_posix(),
                simulate=False,
            )
        logging.info(
            "Linking and conversion process successful. Output files are available at '%s'", args.output_directory
        )
    else:
        logging.info("Linking process successful. Output files are available at %s.", args.output_directory)
        logging.info("Please run the chakra_converter for further postprocessing.")


if __name__ == "__main__":
    main()
