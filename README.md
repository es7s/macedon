<h1 align="center">
  <img src="https://user-images.githubusercontent.com/50381946/211150260-a91aa0c7-f79b-459c-8a37-a92da96a86a2.png">
  <br>
  <code>macedon</code>
  <br>
</h1>

<p align="center">
    <a href="https://pypi.org/project/macedon/"><img alt="PyPI" src="https://img.shields.io/pypi/v/macedon"></a>
    <a href="https://pepy.tech/project/macedon/">
      <img alt="Downloads" src="https://pepy.tech/badge/macedon">
    </a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
    </a>
</p>

Multi-threaded CLI web service availability verifier. Takes a list of endpoints with optional input dataset, performs series of HTTP requests and displays the results.

## Motivation

Necessity to have a fast and configurable endpoint testing tool at fingertips.

## Installation

    pipx install macedon

## Basic usage

![image](https://user-images.githubusercontent.com/50381946/211187585-2e932cde-f8f6-4d91-9769-962b6efdfe07.png)

## Configuration / Advanced usage

    Usage: python -m macedon [OPTIONS] [ENDPOINT_URL]...
    
    Options:
      -T, --threads INTEGER         Number of threads for concurrent request making. Default value depends on number of
                                    CPU cores available in the system.  [default: 6]
      -n, --amount INTEGER          How many times each request will be performed.  [default: 1]
      -d, --delay FLOAT             Seconds to wait between requests.  [default: 0]
      -t, --timeout FLOAT           Seconds to wait for the response.  [default: 10]
      -f, --file FILENAME           Execute request(s) from a specified file. The file should contain a list of endpoints
                                    in the format '{method} {url}', one per line. Another supported (partially) format is
                                    JetBrains HTTP Client format, which additionally allows to specify request headers and
                                    body. The option can be specified multiple times. The ENDPOINT_URL argument(s) are
                                    ignored if this option is present.
      -c, --color / -C, --no-color
      --show-id
      --show-error
      -v, --verbose                 Increase details level: -v for request info, -vv for debugging worker threads
                                    debugging, -vvv for response tracing  [0<=x<=3]
      --help                        Show this message and exit.



## Changelog

[CHANGES.rst](CHANGES.rst)
