# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.5.2] - 2018-03-22
### Changed
- fix PVE files parser to handle values with spaces correctly

## [0.5.1] - 2018-03-20
### Changed
- order vms considered for migration by hash as well

## [0.5.0] - 2018-02-08
### Changed
- migration don't run from or to a node consecutively anymore so when
  limiting the number of migrations, it is more likely they will have
  different source or target nodes

## [0.4.2] - 2018-02-07
### Changed
- consider 'U' in rrd values as unknown value instead of trying to
  convert it

## [0.4.1] - 2018-02-05
### Changed
- fix calling vmiostat function which got the program name

## [0.4.0] - 2018-01-29
### Added
- add custom exceptions and handling
- add --ignore option to ignore some nodes as migration targets

### Changed
- fix parsing of vmiostat command to fix empty help message

## [0.3.0] - 2018-01-10
### Changed
- split vmiostat into its own executable
- multiple nodes can be flushed at once

## [0.2] - 2017-06-02
### Added
- vmiostat subcommand
- changelog
- verbosity flag for migration subcommands is now handled correctly

### Changed
- python version fixed to python 2
- condensed collectd contrib files into pvecollectd module
- Formatting of multi-line argument list of functions
- status overview redesigned
- plan migrations based on used memory ratio instead of absolute size
- read VM stats from .rrd file instead from API
- read HA config from files instead of API

## [0.1] - 2017-03-27
### Added
- inital release
