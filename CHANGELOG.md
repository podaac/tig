# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security


## [0.4.0]

### Added
- **PODAAC-5016**
  - TIG does not decode time values when opening dataset to support SMAP_RSS_L2_SSS_V5
- **PODAAC-4986**
  - TIG includes group names in output image filenames
### Changed
### Deprecated
### Removed
### Fixed
- **PODAAC-4332**
  - Fix no fill value for variables by adding fill value to configuration files
-- **Lock Matlibplot**
  - Lock matlibplot to 3.5.1 
### Security

## [0.3.1]

### Added
### Changed
### Deprecated
### Removed
### Fixed
- **tig-fix**
  - parallelize tig lambda to 2 process, and fix swot ops deployment
### Security


## [0.3.0]

### Added
- **PODAAC-4179**
  - Added in ability to download palette files from hitide url and removed palette folder.
  - Update python libraries.
  - Add TIG cli.
- **PODAAC-4240**
  - TIG handles variables in nested groups.
  - CLI "--input_file" option can now be an absolute path.
- **PODAAC-4422**
  - Update TIG to use python 3.8.
  - Update python libraries.
  - Update TIG input and output to be compatible with cumulus 11.
- **PODAAC-4424**
  - Update tig uploaded images to give bucket account owner full control.
### Changed
### Deprecated
### Removed
### Fixed
### Security


## [0.2.0]

### Added
- **PODAAC-3608**
  - Added in the options to download configuration files from a url.
### Changed
### Deprecated
### Removed
### Fixed
- **PODAAC-3701**
  - Make TIG work with AQUARIUS_L2_SSS_V5 collection, change dataset to open with groups.
- **PODAAC-3720**
  - Add in function to delete every file and folder in temp folder.
### Security


## [0.1.0]

### Added
  - New project

- **PODAAC-3004**
  - Implementation of download and upload of S3 files.

- **PODAAC-3007**
  - Implementation of wrapping tig in run cumulus framework.
  
- **PODAAC-3130**
  - Image generator downloading 
  
- **PODAAC-3003**
  - Initial working version of tig module

- **PODAAC-3172**
  - Faster image generation

- **PODAAC-3006**
  - Jenkins to build terraform and lambda image

- **PODAAC-3008**
  - Terraform file for cumulus to make tig lambda

- **PODAAC-3274**
  - Made TIG lambda into an ecs task

- **PODAAC-3525
  - Added ability to run tig as a fargate taskß

### Changed
- **PODAAC-3366**
  - Migrate to cumulus V8.0.0
### Deprecated
### Removed
### Fixed
- **hotfix-get_lon_lat_grids**
  - Fixed get_lon_lat_grids function where its possible the returned array is greater than col or row size
### Security
