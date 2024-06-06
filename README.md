<h1 align="center">
   <!-- es7s/macedon -->
   <a href="##"><img align="left" src="https://s3.eu-north-1.amazonaws.com/dp2.dl/readme/es7s/macedon/logo.png?v=2" width="96" height="96"></a>
   <a href="##"><img align="center" src="https://s3.eu-north-1.amazonaws.com/dp2.dl/readme/es7s/macedon/label.png" width="200" height="64"></a>
</h1>
<div align="right">
  <a href="##"><img src="https://img.shields.io/badge/python-3.10-3776AB?logo=python&logoColor=white&labelColor=333333"></a>
  <a href="https://pepy.tech/project/macedon/"><img alt="Downloads" src="https://pepy.tech/badge/macedon"></a>
  <a href="https://pypi.org/project/macedon/"><img alt="PyPI" src="https://img.shields.io/pypi/v/macedon"></a>
  <a href='https://coveralls.io/github/es7s/macedon?branch=master'><img src='https://coveralls.io/repos/github/es7s/macedon/badge.svg?branch=master' alt='Coverage Status' /></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a href="##"><img src="https://wakatime.com/badge/user/8eb9e217-791b-436f-b729-81eb63e84b08/project/1d26a427-aecb-4192-965d-119e9a86cdd9.svg"></a>
</div>
<br>

Multi-threaded CLI web service availability verifier. Takes a list of endpoints with optional input dataset, performs series of HTTP requests and displays the results.

<blockquote>
 <details>
  <summary><b>Motivation</b></summary>
  Necessity to have a fast and configurable endpoint testing tool at fingertips.
 </details>
</blockquote>

Installation
--------------

#### With [pipx](https://github.com/pypa/pipx)
```bash
$ pipx install macedon
```

#### Manually
```bash
$ git clone https://github.com/es7s/macedon.git
$ cd macedon
$ python -m venv venv
$ ./venv/bin/pip install .
$ ln -s $(pwd)/run ~/.local/bin/macedon
```

Basics
------------

In the following example we are telling the application to make 4 sequential requests to `192.168.1.2` on port 80 (`GET /` by default);
the number of threads is determined automatically by the number of logical cores of host CPU (`-T` option overrides this number).

![image](https://user-images.githubusercontent.com/50381946/211187585-2e932cde-f8f6-4d91-9769-962b6efdfe07.png)
                                                                     

Options
---------------

    Usage:

       macedon [OPTIONS] [ENDPOINT_URL]...

    Options:
      -T, --threads INTEGER         Number of threads for concurrent request making. Default value depends on number of
                                    CPU cores available in the system.  [default: 6]
      -n, --amount INTEGER          How many times each request will be performed.  [default: 1]
      -d, --delay FLOAT             Seconds to wait between requests.  [default: 0]
      -t, --timeout FLOAT           Seconds to wait for the response.  [default: 10]
      -i, --insecure                Ignore invalid/expired certificates when performing HTTPS requests.
      -f, --file FILENAME           Execute request(s) from a specified file, or from stdin, if FILENAME is specified as
                                    '-'. The file should contain a list of endpoints in the format '{method} {url}', one
                                    per line. Another (partially) supported format is JetBrains HTTP Client format (see
                                    below), which additionally allows to specify request headers and/or body. The option
                                    can be specified multiple times. Note that ENDPOINT_URL argument(s) are ignored if
                                    this option is present.
      -x, --exit-code               Return different exit codes depending on completed / failed requests. With this option
                                    exit code 0 is returned if and only if each request was considered successful (1xx,
                                    2xx HTTP codes); even one failed request (4xx, timed out, etc) will result in a non-
                                    zero exit code. (Normally the exit code 0 is returned as long as the application
                                    terminated under normal conditions, regardless of an actual HTTP codes; but it can
                                    still die with a non-zero code upon invalid option syntax, etc).
      -c, --color / -C, --no-color  Force output colorizing using ANSI escape sequences or disable it unconditionally. If
                                    omitted, the application determines it automatically by checking if the output device
                                    is a terminal emulator with SGR support.
      --show-id                     Print a column with request serial number.
      --show-error                  Print a column with network (not HTTP) error messages, when applicable.
      -v, --verbose                 Increase verbosity:
                                        -v for request details and exceptions;
                                       -vv for request/response contents and headers;
                                      -vvv for exception stack traces and thread state transitions.
      -V, --version                 Show the version and exit. Specify twice (-VV) to see interpreter and entrypoint
                                    paths. If stdout is not a terminal, print only app version number without labels or
                                    timestamps.
      --help                        Show this message and exit.
    

Headers, body, authorization
----------------------------

Request metadata can be specified using **JetBrains [HTTP syntax](https://jetbrains.com/help/idea/exploring-http-syntax.html)** (note that support is [very limited](#http-syntax)) using either:

1. a helper data file (see [example.http](./example.http)):

   ```bash
   $ macedon -T1 -vv -f req1.http
   ```

2. `bash` and *stdin* (all three commands are equivalent):

   ```bash
   $ macedon -f - <<<$'GET http://2ip.ru\nUser-Agent: curl/7.68.0'
   
   $ macedon -f - <<<'GET http://2ip.ru
   User-Agent: curl/7.68.0'
   
   $ echo -e 'GET http://2ip.ru \n User-Agent: curl/7.68.0' | macedon -f -
   ```
   
### HTTP Syntax

Supported features include:

   * Method (GET/POST/etc)
   * Request headers
   * Request body
   * `#` comments

General syntax:

```
# Request name / description (optional)
Method Request-URI
Header-field: Header-value

Request-Body
```


Proxy configuration
--------------------

The application is based on Python [requests](https://pypi.org/project/requests) library that manages all of low-level request handling, which includes proxy support, so that opens up a possibility to test the connectivity to proxies as well. Proxy configuration is done using environment variables. Below is a mini-tutorial on querying the remote server through local SOCKS proxy, but it shall work with regular HTTP/S proxies as well.

First let's create a file with request data, specifically -- with HTTP headers, as a lot of services are suspicious to the requests that came not from a regular browser, but from some custom software, and redirect them to some crazy captchas or just respond with 4XXs.

*req1.http*
```http request
GET http://2ip.ru
User-Agent: curl/7.68.0
```

Now, let's perform a direct request. Some `-v` options were added to examine the actual response from the server, which should contain our external IP address.

> <small><i>The main reason of my regular usage of this service is that it's the fastest way to check your real external IP address from literally everywhere with only one requirement (curl), and it's very easy to memorize: `curl 2ip.ru`</i></small>

```bash
$ macedon -T1 -vv -f req1.http 
```

```console
[INFO ][macedon:#0](+117ms) Request #1: GET http://2ip.ru
[INFO ][macedon:#0](+338ms) Response #1: HTTP 200 OK
[TRACE][macedon:#0](+339ms) 
# [R/R 1]
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> GET http://2ip.ru
> User-Agent: curl/7.68.0

<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
< HTTP 200 OK
< Connection: keep-alive
< Content-Length: 14
< Content-Type: application/octet-stream
< Date: Tue, 28 Nov 2023 18:32:35 GMT
< Server: nginx

185.243.218.152
```

Direct requests work, yay. Next, to use a proxy server define the environment variables **HTTP_PROXY** and **HTTPS_PROXY** in the following format:

```bash
$ export HTTP_PROXY="<protocol>://<user>:<pass>@<proxy>:<port>"
$ export HTTPS_PROXY="<protocol>://<user>:<pass>@<proxy>:<port>"
```

Needless to say that you shall put the real credentials instead of placeholders, but just in case... 

Personally I prefer another method: prepending the command with an environment variable, which sets it as well, but for the one command only. Let's try it:

```bash
$ HTTP_PROXY=socks5h://localhost:1080 macedon -f req1.http -vv
```
```console
[INFO ][macedon:#0](+115ms) Request #1: GET http://2ip.ru
[INFO ][macedon:#0](+1.24s) Response #1: HTTP 200 OK
[TRACE][macedon:#0](+1.24s) 
# [R/R 1]
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> GET http://2ip.ru
> User-Agent: curl/7.68.0

<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
< HTTP 200 OK
< Connection: keep-alive
< Content-Length: 14
< Content-Type: application/octet-stream
< Date: Tue, 28 Nov 2023 18:51:01 GMT
< Server: nginx

23.129.64.132
```
The service now sees that we made a request from another address and reflects that in his response. Furthermore, the latency drastically increased (from ~200ms to more than 1s), which also indicates that request was sent through the proxy. 

> <small><i>(logs context) The delay can be calculated from numbers in (parentheses) displaying elapsed time from the application launch.</i></small>

Sometimes using *SOCKS* proxy causes errors (*HTTP(S)* proxies unaffected), which usually look like this: `[ERROR][...] Missing dependencies for SOCKS support` (*sigh*). The solution is to install the missing dependency, namely — `requests[socks]` which is an optional dependency and thus is not installed by default.

#### With [pipx](https://github.com/pypa/pipx)
```bash
$ pipx inject macedon requests[socks]
```

#### Manually
```bash
$ ./venv/bin/pip install requests[socks]
```


## Changelog

[CHANGES.rst](CHANGES.rst)
