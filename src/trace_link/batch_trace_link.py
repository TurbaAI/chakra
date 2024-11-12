import argparse
import logging
import sys
from collections import namedtuple
from pathlib import Path

from .trace_linker import TraceLinker

LinkerArgs = namedtuple("LinkerArgs", ["host_trace_file", "device_trace_file", "output_trace_file_name"])


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


def find_linker_args(
    input_directory: str, host_trace_identifier: str, device_trace_identifier: str, compress: bool
) -> list[LinkerArgs]:
    input_path = Path(input_directory)
    linked_trace_extension = "_linked.json.gz" if compress else "linked.json"
    output_linker_args = []
    host_traces: list[Path] = []
    device_traces: list[Path] = []
    for item in input_path.iterdir():
        if item.is_dir():
            continue
        if host_trace_identifier in item.name:
            host_traces.append(item)
        elif device_trace_identifier in item.name:
            device_traces.append(item)
    for host_trace in sorted(host_traces):
        matching_device_trace = ""
        for i in range(1, len(host_trace.name)):
            matching_device_traces = [trace for trace in device_traces if host_trace.name[0:i] in trace.name]
            if len(matching_device_traces) == 1:
                matching_device_trace = matching_device_traces[0]
                break
        if not matching_device_trace:
            logging.error(f"Could not find matching device trace for host trace '{host_trace.name}'!")
        else:
            output_linker_args.append(
                LinkerArgs(
                    host_trace_file=host_trace.as_posix(),
                    device_trace_file=matching_device_trace.as_posix(),
                    output_trace_file_name=host_trace.name.split(host_trace_identifier)[0] + linked_trace_extension,
                )
            )
    return output_linker_args


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
        required=True,
        help="Directory containing Chakra host and device trace files",
    )
    parser.add_argument(
        "--chakra-host-trace-identifier",
        type=str,
        required=True,
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
        required=True,
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
        type=str,
        required=True,
        help="Path for the output Chakra host + device traces in the JSON format",
    )

    parser.add_argument(
        "--compression",
        type=bool,
        default=True,
        required=False,
        help="Whether or not to use compression for the linked traces",
    )
    parser.add_argument("--log-filename", type=str, default="", help="Debug Log filename")

    args = parser.parse_args()

    setup_logging(args.log_filename)

    linker_args = find_linker_args(
        input_directory=args.input_directory,
        host_trace_identifier=args.chakra_host_trace_identifier,
        device_trace_identifier=args.chakra_device_trace_identifier,
        compress=args.compression,
    )
    if not linker_args:
        logging.error(
            "No trace pairs found (input_dir: '%s', host_trace_identifier: '%s', device_trace_identifier: '%s')",
            args.input_directory,
            args.chakra_host_trace_identifier,
            args.device_trace_identifier,
        )
        sys.exit(-1)

    Path(args.output_directory).mkdir(exist_ok=True, parents=True)
    for idx, linker_arg in enumerate(linker_args):
        output_file = Path(args.output_directory, linker_arg.output_trace_file_name).as_posix()
        logging.info(
            "Linking file pair %d of %d: inputs: ('%s', '%s'), output: '%s'",
            idx + 1,
            len(linker_args),
            linker_arg.host_trace_file,
            linker_arg.device_trace_file,
            output_file,
        )
        linker = TraceLinker()
        linker.link(linker_arg.host_trace_file, linker_arg.device_trace_file, output_file)

    logging.info(f"Linking process successful. Output files are available at {args.output_directory}.")
    logging.info("Please run the chakra_converter for further postprocessing.")


if __name__ == "__main__":
    main()
