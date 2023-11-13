============
Changelog
============

.. default-role:: code

This project uses Semantic Versioning -- https://semver.org

-----------
*<current>*
-----------
- 🐞 FIX: panik on invalid schema url

0.12.0
------

- 💎 REFACTOR: verbose logging
- 🆙 UPDATE: got rid of embedded `pytermor` pkg
- 🆙 UPDATE: `pytermor` updated to 2.106
- 🐞 FIX: dependencies

0.11.0
------

- 💎 REFACTOR: exception logging, input file handling
- 🧪 TESTS: fixed coverage counting
- 🔧 MAINTAIN: `update-help-usage` script

0.10.0
------

- 🌱 NEW: `--exit-code` option
- 📙 DOCS: add proxy configuration guide

0.9.11
------

- 🐞 FIX: full output when no terminal attached
- 🌱 NEW: `--insecure` option

0.9.10
-------

- 🐞 FIX: broken dependency

0.9.9
-------

- 🌱 NEW: automatic calculation of default threads number
- 🌱 NEW: TRACE logging level

0.9.8
-------

- 💎 REFACTOR: `Worker` and `Printer` classes and error output formatting

0.9.7
-------

- 🐞 FIX: division by 0 error when invoking with some options, but without arguments

0.9.6
-------

- Temporarily included `pytermor` as bundled package because 2.x is still in "dev" status.
- 🐞 FIX: average request latency calculation when all requests failed


0.9.5
-------

- Implementation of all intended features.


0.9.0 `                Jan 23`
------------------------------

- Core
