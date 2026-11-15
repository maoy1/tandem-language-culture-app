# #108 — stable registration form width (v1)

Owner measured, at the same window size:

| State | Columns | Form width | Learn-language card width |
|---|---:|---:|---:|
| Startup View | 2 | 916 | 458 |
| After entering Edit | 2 | 1303 | 458 |

Columns did not change; available form width did. The preserved native baseline
has MainContainer1.LayoutAlignItems=Start and no explicit Form1.Width source
binding (runtime default 800). These are baseline observations, not proof of the
exact layout-engine cause. Bind width to the parent and stretch the container's
children so sizing is reactive in View and Edit.

## Apply in the current Studio app

Use the working native app with existing registration fixes and your current
field order. Preserve its saved version/export. No app/Solution/flow import.

1. Tree view: select **MainContainer1**, the inner container that contains Form1
   and ValidationFooter. Choose **LayoutAlignItems** in the top property dropdown;
   paste `MainContainer1.LayoutAlignItems.fx`:
   `LayoutAlignItems.Stretch`.
2. Select **Form1**, choose **Width** in the top property dropdown/formula bar;
   paste `Form1.Width.fx`: `Parent.Width`.

Use the formula bar rather than the numeric width box. Keep Columns=2, your
data-card X/Y/Width settings, Form1.Visible and the empty-state label unchanged.
The inner container's existing horizontal padding is zero in the baseline.

## Owner native check — NOT RUN until returned

- [ ] Same desktop window size: fresh Preview starts with two columns in View.
  Record the existing diagnostic's form width; click pencil and record again.
  Expect approximately the same available width, without a View→Edit jump.
- [ ] Save and Cancel return to the same two-column layout; navigate away/back
  and confirm the layout is stable. Preserve your requested field order and
  single-row Time zone arrangement.
- [ ] Existing own-profile data, catalogue choices/search, identity and navigation
  work as before. Restore any harmless saved test edit.
- [ ] With the existing approved no-profile fixture, the empty hint/New/Cancel
  behavior remains correct. Missing fixture is BLOCKED; do not delete a working
  profile just for this check.
- [ ] Check the intended phone layout, which may use a narrower arrangement;
  do not interpret desktop two-column acceptance as a mobile accessibility claim.

Check App checker, then Save → Publish the same app; close old player tabs and
verify the normal app too. Temporary diagnostic labels can be removed after
recording the measurements. Preserve the native export without repacking.
Return PASS/FAIL, before/after widths and exact errors without personal values.

Local baseline/property/package/hash checks are not native Studio/runtime PASS.
This changes presentation sizing only: no data fields, modes, own-profile/empty/
New guards, save callbacks, validation, identity, shared rules or flow IO changes.
No added network reads, connector or schema. #81 no-impact applies.
