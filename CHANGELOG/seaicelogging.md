# v1.1.1 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v1.1.0 (2017-01-04)

- Add `level_name` parameter to `log_command` so that function arguments can be
  logged at a level other than `INFO`

# v1.0.1 (2017-01-03)

- Fix missing version constraints for dependencies.
- Update readme

# v1.0.0 (2016-12-15)

- Include hostname in log filename. Log filenames now have the format
  `project-name.hostname.log`.
- Rotate logfile to timestampped gzip file by default.

# v0.1.3 (2016-11-18)

- Relocate /share/apps/g02135-sii-asina to /share/apps/seaice
- Relocate /share/logs/g02135-sii-asina to /share/logs/seaice


# v0.1.2 (2016-11-02)

- Package will now output warning and write only to console logger if logfile
  is not writable


# v0.1.1 (2016-10-17)
- Build the package correctly to include the base logging configuration file.

# v0.1.0 (2016-10-06)

- Initial release.
