# Changelog
All notable changes to fwtv module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0)

## [2.4.1] - 2025-07-07

### Fixed

- fixed a bug where the tolerance was not applied correctly when checking the attendances

## [2.4.0] - 2025-06-06

### Added

- ruff and pyright for static code analysis

### Fixed

- add lower bound for dependencies

### Changed

- increase api version

## [2.3.1] - 2023-10-09

### Fixed

- declare `factorialhr` dependency explicitly

## [2.3.0] - 2023-10-09

### Added

- possibility to change the dates from when to when the data is fetched
- possibility to change the timeout for fetching the data

### Fixed

- additional information showed wrong information, if the table contained more than one error

## [2.2.0] - 2023-08-07

## Added

- extra window showing all attendances that lead to this verification failure
- tolerance can be configured though input now

## [2.1.0] - 2023-04-08

### Changed

- Choose between teams and single employee and made combobox editable
- Renamed labels to `Affected Day(s)`, `Cumulated Break` and `Cumulated Attendance`
- Avoid duplications by resetting `current_attendances` list
- Ignore seconds of each attendance, because factorials automated time tracking is not precise

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
