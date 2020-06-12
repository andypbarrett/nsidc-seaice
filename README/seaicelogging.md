seaicelogging
---

**seaicelogging** is a package provided to ensure consistent logging setup
across the [Sea Ice Index
Project](https://bitbucket.org/account/user/nsidc/projects/SI).

# Usage

## In other Python modules

When you are creating a cli command, we need to configure the loggers and
handlers before doing any logging in order to get the expected output.

	 source
	 ├── packagename
	 │   ├── cli
	 │   │   └── command.py
	 │   ├── module.py


When you have a python package laid out as above and want to use
`seaicelogging`, you just import it and call init in your cli program, and that
will set up loggers and handlers according to the setup in this package's
`logging.yml`.

In the cli module you get a logger (`log`) by calling `seaicelogging.init` with
the package-name as the only parameter.

```
#!python
# command.py

import seaice.logging as seaicelogging

log = seaicelogging.init('packagename')

@seaicelogging.log_command(log)
def command():
	do_stuff
	log.debug('debug log message in the cli command')

if __name__ == '__main__':
   command()
```

In cli-program support modules like `module.py`, just use standard logging with
`__name__`.

```
#!python
# module.py

import logging
log = logging.getLogger(__name__)

def helper():
	log.info('info message inside helper')

```

In non-CLI packages (libraries) we follow the best practices for python which is
to be sure to add a `NullHandler` and work only with
`logging.getLogger(__name__)`.

```
#!python
# __init__.py

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
```

And in modules the same as for support modules as above.
```
#!python
import logging
log = logging.getLogger(__name__)

def helper():
	log.info('info message inside helper')
```

### Customizations

* output log file: The default location for the log output files is
  `/share/logs/seaice/package-name.log`, but can be overridden by setting the
  environmental variable `LOG_FILE` to full path to the desired output log file.

* default log level: for the package is set to `INFO` in the `logging.yml` file,
  but can be overridden by setting the environmental variable `LOG_LEVEL` to one
  of [python's default logging
  levels](https://docs.python.org/2.6/library/logging.html#logging-levels).
  Setting this log level only effects the package logging, any libraries are
  still set to the `ROOT_LOG_LEVEL`.

* root logging level: If you want to change the logging level for imported
  libraries, you can set the environmental variable `ROOT_LOG_LEVEL`. which
  controls the logging level of the root handler.
