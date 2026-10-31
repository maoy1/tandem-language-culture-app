# Application code

Place application and domain code in this directory. Keep business rules
independent from Power Apps and SharePoint connector details where practical so
they can be tested and moved later.

`tandem/discovery.py` implements initial eligibility using normalized trusted
records and positive integer Language catalogue lookup IDs. It supports one-way
and reciprocal exchanges, excludes self/non-Active profiles and has no writes.
Run its scenarios with `python -m pytest tests/test_discovery.py` from the repo.
It is a local business-rule module, not an app endpoint or authorization layer.
Power Apps cannot invoke this Python module directly: an approved runtime/data
adapter and deployment are still needed; do not assume hosting or permissions.
