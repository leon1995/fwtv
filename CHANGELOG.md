# Changelog
All notable changes to fwtv module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0)

## [1.1.0] - 2023-03-10

### Changed

- Allow 6 or 9 hours and 1 minute of working time before adding it as an error. This is because the automated clock in/out system of factorial requires some seconds to progress resulting in a work time of 6 or 9 hours and some seconds, even though you have set the automated clock in/out to 6 or 9 hours