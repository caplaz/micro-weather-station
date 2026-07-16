# Rain-rate device-class compatibility

## Goal

Allow the rain-rate configuration field to show Ecowitt WS90-style sensors that
report a rain rate but are labelled with Home Assistant's `precipitation`
device class, without changing rain-rate processing or forecasting behavior.

## Scope

The initial setup and options flows will use the same entity-selector filter:

```python
domain="sensor",
device_class=["precipitation_intensity", "precipitation"],
```

This keeps `precipitation_intensity` as the primary class while making
misclassified, rate-valued `precipitation` sensors selectable.

No conversion, validation, condition-detection, or forecast logic changes are
included. The integration already reads the selected entity's unit and
converts rain rate for analysis; this issue is solely about selector discovery.

## Safety and compatibility

Home Assistant normally uses `precipitation` for accumulated rainfall and
`precipitation_intensity` for rates. The selector cannot filter by units, and
the flow already accepts manually entered sensor IDs without checking their
device class. Supporting both classes therefore restores access to the WS90
sensor without adding a new validation path or rejecting existing setups.

## Tests

Add focused config-flow tests for both forms. Each will inspect the rain-rate
entity selector and assert it accepts the two supported device classes in the
defined order. Existing submission behavior remains covered by the current
options-flow test.
