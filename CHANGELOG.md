# CHANGELOG 

## v0.2.0 (2024-01-01)

### Feature

* feat(flysight2csv): new cli, merge files, valid_offset flag

* rewrite CLI and separate argument parsing from program logic
* also merge reformatted SENSOR.CSV and TRACK.CSV files into a MERGED.CSV
* add valid_offset flag to reformatted files (False if datetime is invalid) ([`a881dd4`](https://github.com/yoleg/flysight2csv/commit/a881dd4eb7ca02a491d266d5b5bd2745fa9b3f58))

## v0.1.1 (2023-12-30)

### Feature

* feat(flysight2csv): initial release ([`566d748`](https://github.com/yoleg/flysight2csv/commit/566d7487b1873485ea43a71a34fe40e10040b4f4))

### Fix

* fix(parser): fix duplicate time column names ([`1a86835`](https://github.com/yoleg/flysight2csv/commit/1a86835b108ae754d065d1757b184c1735a698ba))

