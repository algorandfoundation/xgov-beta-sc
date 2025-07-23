# Testing

xGov Architecture uses the PyTest framework for unit tests and end-to-end tests.

PyTest fixtures are organized hierarchically in the `tests` folder: fixtures defined
in the `conftest.py` file at higher levels are available to all the nested-level
tests.
