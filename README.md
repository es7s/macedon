<h1 align="center">
  <img src="https://user-images.githubusercontent.com/50381946/167810957-14b78013-00cf-436e-b535-d2b89f881c44.png">
  <br>
  <code>
    macedon
  </code>
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

Web-service availability verifier. Takes a list of endpoints with optional input dataset and expected output HTTP status codes/responses, performs series of HTTP requests and displays the results.

## Motivation

Necessity to have a fast and configurable endpoint testing tool at fingertips.

## Installation

    pipx install macedon

## Basic usage

    > macedon localhost:5000
    200  4.16kb  0.204s  http://localhost:5000

## Configuration / Advanced usage



## Changelog

### v0.0.1

- Core
