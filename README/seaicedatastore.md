seaicedatastore
---

**seaicedatastore** provides an API for reading and writing a sea ice datastore
(created by processing in the `sedna` subpackage).  The datastore contains area,
extent and other statistical/QA information for each day/hemisphere for the 0081
and 0051 products.

![seaicedatastore](doc/seaicedatastore.png)


# Usage

## In other Python modules

```
#!python
import seaice.datastore as sds
```
