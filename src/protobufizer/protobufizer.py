import argparse

import orjson
from google.protobuf.json_format import ParseDict
from tqdm import tqdm

from ...schema.protobuf.et_def_pb2 import (
    GlobalMetadata,
)
from ...schema.protobuf.et_def_pb2 import (
    Node as ChakraNode,
)
from ..third_party.utils.protolib import encodeMessage as encode_message
from ..utils.file_io import open_file_read, open_file_write


def main() -> None:
    parser = argparse.ArgumentParser(description="Converts Chakra execution trace in JSON format to ET format.")
    parser.add_argument(
        "--input-filename",
        type=str,
        required=True,
        help="Specifies the input filename of the jsonized Chakra execution trace.",
    )
    parser.add_argument(
        "--output-filename", type=str, required=True, help="Specifies the output filename for the ET data."
    )
    args = parser.parse_args()

    with open_file_read(args.input_filename, "rb") as file_in, open_file_write(args.output_filename, "wb") as file_out:
        trace_objects = orjson.loads(file_in.read())
        global_metadata = ParseDict(trace_objects[0], GlobalMetadata())
        encode_message(file_out, global_metadata)
        for sub_dict in tqdm(trace_objects[1:], desc="Saving chakra nodes", unit="node"):
            encode_message(file_out, ParseDict(sub_dict, ChakraNode()))


if __name__ == "__main__":
    main()
