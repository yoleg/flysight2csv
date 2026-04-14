# CHANGELOG 

## v0.2.4 (2026-04-14)

### Bug fixes

* fix(program_params): update Pydantic configuration for validation ([`f776116`](https://github.com/yoleg/flysight2csv/commit/f776116f481afcc5465de7beddaad3dc69f1798c))

* fix(parser): fix header validation ([`f60f0c6`](https://github.com/yoleg/flysight2csv/commit/f60f0c6c9ca0c24732ba019b6694d7a12eface67))

## v0.2.3 (2024-01-03)

### Bug fixes

* fix(flysight2csv): clarify ambiguous arg name ([`4c08389`](https://github.com/yoleg/flysight2csv/commit/4c083898d51463340c7f717ba92ea8734aa9f562))

## v0.2.2 (2024-01-03)

### Bug fixes

* fix(reformat): fix jsonl extension ([`53af47e`](https://github.com/yoleg/flysight2csv/commit/53af47e4e852e50a3281765e34f0ce19da2d9cbe))

## v0.2.1 (2024-01-03)

### Bug fixes

* fix(program): avoid merge logs on simple copy ([`049aac7`](https://github.com/yoleg/flysight2csv/commit/049aac750be99d402589bc1f7001eaa441001fe2))

## v0.2.0 (2024-01-01)

### Features

* feat(flysight2csv): new cli, merge files, valid_offset flag

* rewrite CLI and separate argument parsing from program logic
* also merge reformatted SENSOR.CSV and TRACK.CSV files into a MERGED.CSV
* add valid_offset flag to reformatted files (False if datetime is invalid) ([`a881dd4`](https://github.com/yoleg/flysight2csv/commit/a881dd4eb7ca02a491d266d5b5bd2745fa9b3f58))

## v0.1.1 (2023-12-30)

### Bug fixes

* fix(parser): fix duplicate time column names ([`1a86835`](https://github.com/yoleg/flysight2csv/commit/1a86835b108ae754d065d1757b184c1735a698ba))

## v0.1.0 (2023-12-29)

### Features

* feat(flysight2csv): initial release ([`566d748`](https://github.com/yoleg/flysight2csv/commit/566d7487b1873485ea43a71a34fe40e10040b4f4))
