# [0.2.2] - 2026-04-20
* Default global client — `Template` now uses a shared process-wide `PyHandlebars` instance when no `client=` is passed, so partials and helpers are shared across templates without explicit wiring.
* `PyHandlebars.helper` decorator at the class level registers helpers on the global client (no instance needed).

# [0.2.1] - 2026-03-31
* Remove benchmarks from repo and move to [sukram42/python-templating-benchmarks](https://github.com/sukram42/python-templating-benchmarks)

# [0.2.0] - 2026-03-31
* Decorator for helper functions.

# [0.1.1] - 2026-03-09
* Adding meta information to the package.

# [0.1.0] - 2026-03-09
* Initial setup.