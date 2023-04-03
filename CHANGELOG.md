# Changelog
All notable changes to fwtv module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0)

## [2.0.1] - 2023-04-03

### Added

- Added missing dependencies

### Changed

- Restructured project to use src layout
- Test built package and not sources

## [2.0.0] - 2023-03-27

### Changed

- Terminal output has been replaced by a `pyside6` application

### Removed

- Removed support for older versions than `3.11`

## [1.1.0] - 2023-03-10

### Changed

- Allow 6 or 9 hours and 1 minute of working time before adding it as an error. This is because the automated clock in/out system of factorial is inaccurate and does not exactly clock out after 6 or 9 hours