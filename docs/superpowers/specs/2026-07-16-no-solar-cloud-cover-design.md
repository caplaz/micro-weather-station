# No-Solar Cloud-Cover Detection Design

## Goal

Prevent absent solar inputs from being interpreted as complete cloud cover, and
make the solar-model test suite deterministic across calendar dates.

## Current behavior

The daytime condition analyzer receives a solar elevation from `sun.sun` even
when no radiation, lux, or UV sensor is configured. It then passes three zero
values to `SolarAnalyzer`, which correctly treats *measured* zero light as
overcast but cannot distinguish it from missing sensor data. This reports
`cloudy` on clear days.

One solar test calls the seasonal clear-sky model using the live clock while
asserting a fixed numeric output. Its expected value drifts as the day of year
changes.

## Design

`WeatherConditionAnalyzer._determine_daytime_condition` will use its existing
atmospheric fallback whenever none of radiation, lux, or UV has a positive
reading. This check occurs before solar elevation is used, so an optional
`sun.sun` entity provides time-of-day information only; it does not turn
missing measurement sources into zero-light measurements.

Real zero readings remain unchanged: the solar analyzer continues to map a
configured sensor reporting zero radiation/lux/UV to complete cloud cover.

The regression test will construct a clear, high-pressure daytime sample with
a valid solar elevation and no solar inputs, and assert `sunny`. A companion
test keeps the all-zero solar-analyzer behavior at 100% coverage. The
date-sensitive low-radiation test will call the clear-sky calculation through a
fixed date, eliminating calendar-dependent assertion drift without modifying
production calculations.

## Error handling and compatibility

No configuration schema or entity changes are needed. The existing fallback
remains responsible for uncertainty when all solar sources are absent, and
precipitation, fog, and severe-weather priorities continue to run before this
daytime branch.

## Verification

Run the new regression tests first to observe their failures, implement the
minimal routing change and fixed-date test setup, then run the focused solar and
core suites, the CI-targeted detector/validation tests, and the full suite.
