# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
