-- GoogleSQL template. NOT executed while preparing this kit.
-- Inspect source schema and partition metadata and perform a dry run first.
-- Named parameters are INT64 YYYYMMDDHHMMSS boundaries in UTC.
-- Half-open DATEADDED bounds are mandatory. Do not replace with SQLDATE.
-- This canonical template intentionally does not guess partition semantics.
-- Add verified partition pruning in a rendered query only after its safety is proved.
-- Required columns are selected; LIMIT is not a scan-cost control.
SELECT
  CAST(GLOBALEVENTID AS STRING) AS GlobalEventID,
  CAST(SQLDATE AS STRING) AS SQLDATE,
  CAST(DATEADDED AS STRING) AS DATEADDED,
  Actor1CountryCode,
  Actor2CountryCode,
  EventCode
FROM `gdelt-bq.gdeltv2.events`
WHERE DATEADDED >= @start_dateadded
  AND DATEADDED < @end_dateadded
  AND EventCode = '061'
