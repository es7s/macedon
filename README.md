<div align="center">
   <img src="https://user-images.githubusercontent.com/50381946/211150260-a91aa0c7-f79b-459c-8a37-a92da96a86a2.png" width="96" height="96"><br>
   <img src="https://user-images.githubusercontent.com/50381946/219900319-d335e85f-5449-4bcf-8f3b-b56eb88f2246.png" width="400" height="64">
</div>

<div align="center">
  <img src="https://img.shields.io/badge/python-3.10-3776AB?logo=python&logoColor=white&labelColor=333333">
  <a href="https://pepy.tech/project/macedon/">
    <img alt="Downloads" src="https://pepy.tech/badge/macedon">
  </a>
  <a href="https://pypi.org/project/macedon/"><img alt="PyPI" src="https://img.shields.io/pypi/v/macedon"></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</div>
<h1> </h1>


Multi-threaded CLI web service availability verifier. Takes a list of endpoints with optional input dataset, performs series of HTTP requests and displays the results.

## Motivation

Necessity to have a fast and configurable endpoint testing tool at fingertips.

## Installation

    pipx install macedon

## Basic usage

![image](https://user-images.githubusercontent.com/50381946/211187585-2e932cde-f8f6-4d91-9769-962b6efdfe07.png)

## Configuration / Advanced usage

    Usage: macedon [OPTIONS] [ENDPOINT_URL]...
    
    Options:
      -T, --threads INTEGER         Number of threads for concurrent request making. Default value depends on number of
                                    CPU cores available in the system.  [default: 6]
      -n, --amount INTEGER          How many times each request will be performed.  [default: 1]
      -d, --delay FLOAT             Seconds to wait between requests.  [default: 0]
      -t, --timeout FLOAT           Seconds to wait for the response.  [default: 10]
      -i, --insecure                Skip certificate verifying on HTTPS connections.
      -f, --file FILENAME           Execute request(s) from a specified file. The file should contain a list of endpoints
                                    in the format '{method} {url}', one per line. Another supported (partially) format is
                                    JetBrains HTTP Client format, which additionally allows to specify request headers an
                                    body. The option can be specified multiple times. The ENDPOINT_URL argument(s) are
                                    ignored if this option is present.
      -x, --exit-code               Return different exit codes depending on completed / failed requests. With this optio
                                    exit code 0 is returned if and only if each request was considered successful (1xx,
                                    2xx HTTP codes); even one failed request (4xx, timed out, etc) will result in a non-
                                    zero exit code. (Normally the exit code 0 is returned as long as the application
                                    terminated under normal conditions, regardless of an actual HTTP codes; but it can
                                    still die with a non-zero code upon invalid option syntax, etc).
      -c, --color / -C, --no-color  Force output colorizing using ANSI escape sequences or disable it unconditionally. If
                                    omitted, the application determine it automatically by checking if the output device
                                    is a terminal emulator with SGR support.
      --show-id                     Print a column with request serial number.
      --show-error                  Print a column with error details (when applicable).
      -v, --verbose                 Increase details level: -v for request info, -vv for debugging worker threads, -vvv
                                    for response tracing  [0<=x<=3]
      --help                        Show this message and exit.                                                          

## Proxy configuration

The application is based on Python [requests](https://pypi.org/project/requests) library that manages all of low-level request handling, which includes proxy support, so that opens up a possibility to test the connectivity to proxies as well. Proxy configuration is done using environment variables. Below is a mini-tutorial on querying the remote server through local SOCKS proxy, but it shall work with regular HTTP/S proxies as well.

First let's create a file with request data, specifically -- with HTTP headers, as a lot of services are suspicious to the requests that came not from a regular browser, but from some custom software, and redirect them to some crazy captchas or just respond with 4XXs.

File *"req1.http"*:
```http request
GET http://2ip.ru
User-Agent: curl/7.68.0
Accept: */*
Accept-Encoding: gzip
```

Now, let's perform a direct request. I added some `-v` options to examine the actual response from the server, which should contain our external IP address. <small>*The main reason why I'm regularly using this service -- it's the fastest way to check your external IP address from literally everywhere with just a working terminal being required, and it's very easy to memorize: `curl 2ip.ru`*</small>.

```console
$ macedon -T1 -f req1.http -vvv
...
   200    16b  105ms  GET http://2ip.ru                                                                               
 [ 100% 1/1 ] [INFO ][macedon:#0](+201ms) Response #1 metadata: 200 {'Server': 'nginx', 'Date': 'Fri, 09 Jun 2023 14:44:23 GMT', 'Content-Type': 'application/octet-stream', 'Content-Length': '16', 'Connection': 'keep-alive'}
[TRACE][macedon:#0](+201ms) 
Response #1 content:_____________________________________________________
  0 |U+ 31 38 35 2E 32 34 33 2E 32 31 38 2E 31 35 32 0A |185.243.218.152↵
----------------------------------------------------------------------(16)
 ...
```

Direct requests work, yay. Next, to use a proxy server define the environment variables **HTTP_PROXY** and **HTTPS_PROXY** in the following format:

```console
$ export HTTP_PROXY="http://<user>:<pass>@<proxy>:<port>"
$ export HTTPS_PROXY="http://<user>:<pass>@<proxy>:<port>"
```

Needless to say that you shall put the real credentials instead of placeholders, but just in case... 

Personally I prefer another method: prepending the command with an environment variable, which sets it as well, but for the one command only. Let's try it:

```console

$ HTTP_PROXY=socks5h://localhost:1080 macedon -f req1.http -vvv
...
  200    14b  964ms  GET http://2ip.ru                                                                               
 [ 100% 1/1 ] [INFO ][macedon:#0](+1.06s) Response #1 metadata: 200 {'Server': 'nginx', 'Date': 'Fri, 09 Jun 2023 14:49:24 GMT', 'Content-Type': 'application/octet-stream', 'Content-Length': '14', 'Connection': 'keep-alive'}
[TRACE][macedon:#0](+1.07s) 
Response #1 content:_______________________________________________
  0 |U+ 32 33 2e 31 32 39 2e 36 34 2e 31 33 32 0a |23.129.64.132↵  
---------------------------------------------------------------(14)
```
The service now sees that we made a request from another address and reflects that in his response. Furthermore,  the latency drastically increased from 105 ms to almost 1 second, which can also be considered as confirmation of successful proxying the request.

There is also a possibility to encounter errors while attempting to connect through *SOCKS* proxy (*HTTP* proxies unaffected), which usually look like this: `[ERROR][macedon:#0](+92.9ms) Missing dependencies for SOCKS support` (*sigh*). Well, there is an easy solution for this: just install the missing depenedencies:

```console
pipx inject macedon requests[socks]
```

This is an optional dependency and due to this it's not installed by default. If `pipx` is not present, it's also can be done manually with `venv/bin/pip` (assuming the `virtualenv` is being used instead).

## Changelog

[CHANGES.rst](CHANGES.rst)
