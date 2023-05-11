
# Multi-sport Tournament Scheduler

An implementation of five schedulers for multi-sport tournaments. It is customisable and works with any knockout tournament regardless of sport.

This, along with a 12,000 word dissertation, formed my Part II Project for my undergraduate degree in the Computer Science Tripos at the University of Cambridge.
## Installation

Install the project by cloning the repo and installing dependencies.

1. Clone the repo
```bash
  git clone https://github.com/Techatonic/part-ii-dissertation.git
  cd part-ii-dissertation
```
2. Install dependencies
```bash
  pip3 install -r requirements.txt
```
    
## Usage/Examples

The program is accessed through a command-line interface (CLI). Through the CLI, you can indicate which solver to run along with an input path and other arguments.

### Usage ###
```
usage: Automated Event Scheduler [-h] --import_path IMPORT_PATH [--export_path EXPORT_PATH] [-c N] [-m] [-b] [-hb N] [-g P G] [-forward_check]


options:
  -h, --help            show this help message and exit
  --import_path IMPORT_PATH
                        read json input from this path
  --export_path EXPORT_PATH
                        export json output to this path
  -c N                  run input_path on constraint checker and allow up to N changed events
  -m                    run on CSP base solver
  -b                    run on CSP backtracking solver
  -hb N                 run on CSOP heuristic_backtracking solver using N schedules for each sport
  -g P G                run on CSOP genetic algorithm solver with iniital population of size P and G generations
  -forward_check        run forward checking algorithm on solver

```

E.g.
```bash
  python3 main.py --import_path examples/inputs/example_input_tight_8.json --export_path examples/outputs/test_output.json -hb 3
```
## License

Distributed under the BSD license

```
BSD 2-Clause License

Copyright (c) 2023, Daniel Leboff

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```