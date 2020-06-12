# v1.0.3 (2017-06-22)

* * Update `nasateam` dependency to >=2.0 for Sea Ice Index v3.0

# v1.0.2 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v1.0.1 (2017-01-03)

- Update README

# v1.0.0 (2016-12-15)

- Initial release; functionally identical to v0.3.0.

# v0.3.0 (2016-11-02)

- Datastore is now written as a serialized representation of the dataframe (e.g. daily.p)
- Fixed 10s dataframe read delay
- Add fixture module to allow datastore-compliant CSVs to be read into a dataframe

# v0.2.0 (2016-10-06)

- Remove parameter `restrict_filename` from function `daily`; there is no reason
  to cut down the filename in `seaicedatastore`, but users of it can still do
  such manipulations.
- Write floats to the datastores with 3 decimal places.

# v0.1.0 (2016-09-13)

- Initial package contains common sea ice data store read/write methods exposed via package api
- Adds an argument to `daily_dataframe` to restrict the filename to current
  date, rather than a list of files used for interpolation.
