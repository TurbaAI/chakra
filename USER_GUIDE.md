# Chakra User Guide
## Installation
### Step 1: Set up a Virtual Environment
It's advisable to create a virtual environment using Python 3.10.2.

```bash
# Create a virtual environment
$ python3 -m venv chakra_env

# Activate the virtual environment
$ source chakra_env/bin/activate
```

### Step 2: Install Chakra
With the virtual environment activated, install the Chakra package using pip.

```bash
# Install package from source
$ pip install .

# Install latest from GitHub
$ pip install https://github.com/mlcommons/chakra/archive/refs/heads/main.zip

# Install specific revision from GitHub
$ pip install https://github.com/mlcommons/chakra/archive/ae7c671db702eb1384015bb2618dc753eed787f2.zip
```

### Step 3: Install PARAM
Installing PARAM is necessary for Chakra to function properly as it imports essential components from it.

```bash
$ git clone git@github.com:facebookresearch/param.git
$ cd param/et_replay
$ git checkout 7b19f586dd8b267333114992833a0d7e0d601630
$ pip install .
```

### Step 4: (optional) Install Rust Extensions
Installing rust extensions significantly speeds up trace linking

```bash
$ apt-get install cargo
$ cd rust/
$ pip install maturin
$ pip install .
```

### Step 4: Uninstalling Chakra
To uninstall Chakra, use the following command within the virtual environment.

```bash
$ pip uninstall chakra
```

## Tools Overview
### Execution Trace Link (chakra_trace_link)
Merge Chakra host execution trace and Chakra device execution trace to encode GPU operators into the output execution trace.
```bash
$ chakra_trace_link \
    --chakra-host-trace /path/to/chakra_host_trace \
    --chakra-device-trace /path/to/chakra_device_trace \
    --output-file /path/to/chakra_host_device_trace.json

```
* --chakra-host-trace: Path to the input Chakra host trace in JSON format.
* --chakra-device-trace: Path to the input Chakra device trace in JSON format.
* --output-file: Path to the output file where the linked Chakra trace will be saved in JSON format.

### Execution Trace Batch Link (chakra_trace_link_batch)
Batch version of `chakra_trace_link`. Provide input and output directories and whether to use compression, as well as "identifiers" (string fragments) which 
identify host and device traces respectively.
```bash
$ chakra_trace_link_batch \
    --input-directory /path/to/trace_files \
    --output-directory /path/to/output \
    --compress \
    --convert \
    --chakra-host-trace-identifier .et.trace.json \
    --chakra-device-trace-identifier .pt.trace.json
```
* --input-directory: Path to the folder where input Chakra host traces and input Chakra device traces are located
* --output-directory: Path to the output directory where the linked Chakra traces will be saved in JSON format.
* --compress: Whether to apply gzip compression to the output files
* --convert: Whether to convert the linked Chakra traces to protobuf format after linking
* --chakra-host-trace-identifier: File name contents by which Chakra host traces can be identified (e.g. `.et.trace.json`)
* --chakra-device-trace-identifier: File name contents by which Chakra device traces can be identified (e.g. `.pt.trace.json`)

### Execution Trace Converter (chakra_converter)
Converts the execution traces from `chakra_trace_link` into traces in the protobuf format. It is responsible for identifying and encoding dependencies for simulation as well. The converter is designed for any downstream simulators that take Chakra execution traces in the protobuf format. It takes an input file in another format and generates a Chakra execution trace output in the protobuf format.
```bash
$ chakra_converter PyTorch \
    --input-filename /path/to/chakra_host_device_trace.json \
    --output-filename /path/to/chakra_trace \
    [--simulate] \
```
* --input-filename: Path to the input file containing the linked Chakra host and device traces in JSON format.
* --output-filename: Path to the output file where the converted Chakra trace will be saved in protobuf format.
* --simulate: (Optional) Enable simulation of operators after the conversion for validation and debugging purposes. This option allows simulation of traces without running them through a simulator. Users can validate the converter or simulator against actual measured values using tools like chrome://tracing or https://perfetto.dev/. Read the duration of the timeline and compare the total execution time against the final simulation time of a trace. Disabled by default because it takes a long time.

### Execution Trace Converter (chakra_converter_batch)
Converts the execution traces from `chakra_trace_link` into traces in the protobuf format. It is responsible for identifying and encoding dependencies for simulation as well. The converter is designed for any downstream simulators that take Chakra execution traces in the protobuf format. It takes an input file in another format and generates a Chakra execution trace output in the protobuf format.
```bash
$ chakra_converter_batch \
    --input-directory /path/to/chakra_linked_traces \
    --output-directory /path/to/output \
    --linked-trace-identifier _linked.json.gz \
    --compress
```
* --input-directory: Path to the input files containing the merged Chakra host and device traces in JSON format.
* --output-directory: Path to the output file where the converted Chakra traces will be saved in protobuf format.
* --linked-trace-identifier: string identifier by which to identify linked traces (.e.g. `_linked.json.gz`)
* --compress: Whether to compress the output chakra protobuf file using gzip.


### Execution Trace Feeder (et_feeder)
The Execution Trace Feeder (et_feeder) is a C++ library designed to feed Chakra traces into any compatible C++ simulator. This library specifically provides dependency-free nodes to a simulator, which must import the feeder as a library. Currently, ASTRA-sim is the only simulator that supports this trace feeder. Below are the commands to run execution traces on ASTRA-sim:
```bash
$ git clone --recurse-submodules git@github.com:astra-sim/astra-sim.git
$ cd astra-sim
$ git checkout Chakra
$ git submodule update --init --recursive
$ cd extern/graph_frontend/chakra/
$ git checkout main
$ cd -
$ ./build/astra_analytical/build.sh -c

$ cd extern/graph_frontend/chakra/
$ python -m chakra.et_generator.et_generator\
    --num_npus <num_npus>

$ cd -
$ ./run.sh
```

### Execution Trace Visualizer (chakra_visualizer)
This tool visualizes execution traces in various formats. Here is an example command:

```bash
$ chakra_visualizer \
    --input-filename /path/to/chakra_et \
    --output-filename /path/to/output.[graphml|pdf|dot]
```

### Execution Trace Jsonizer (chakra_jsonizer)
Provides a readable JSON format of execution traces:

```bash
$ chakra_jsonizer \
    --input-filename /path/to/chakra_et \
    --output-filename /path/to/output_json
```
* --input-filename: Path to the input file containing the Chakra trace in protobuf format.
* --output-filename: Path to the output file where the Chakra trace will be saved in JSON format.

### Execution Trace Protobufizer (chakra_protobufizer)
Converts a JSON representation of a chakra ET back to protobuf:

```bash
$ chakra_protobufizer \
    --input_filename /path/to/chakra_json \
    --output_filename /path/to/output_et
```
* --input-filename: Path to the input file containing the Chakra trace in JSON format.
* --output-filename: Path to the output file where the Chakra trace will be saved in protobuf format.

### Timeline Visualizer (chakra_timeline_visualizer)
Visualizes the execution timeline of traces. This tool serves as a reference implementation for visualizing the simulation of Chakra traces. After simulating Chakra traces, you can visualize the timeline of operator executions. Update the simulator to present when operators are issued and completed. Below is the format needed:
```csv
issue,<dummy_str>=npu_id,<dummy_str>=curr_cycle,<dummy_str>=node_id,<dummy_str>=node_name
callback,<dummy_str>=npu_id,<dummy_str>=curr_cycle,<dummy_str>=node_id,<dummy_str>=node_name
...
```

You can visualize the timeline with the command below.
```bash
$ chakra_timeline_visualizer \
    --input-filename /path/to/input.csv \
    --output-filename /path/to/output.json \
    --num-npus 4 \
    --npu-frequency 1.5GHz
```

When you open the output file with `chrome://tracing`, you will see an execution timeline like the one below.
![](doc/timeline_visualizer.png)

### Compression

All commands dealing with single files can handle compressed files (indicated by the `.gz` extension) automatically for both input and output. For the batch versions of converter and linker, compressed files on the input are handled automatically. For output compression, make sure to pass the `--compress` parameter.