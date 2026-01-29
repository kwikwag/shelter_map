# Contributing

## Adding your municipality

- When adding a new city:
  - Provide a `generate_map` and `download_data` function that adhere to the `City` protocol.
  - Reuse `shelter_map.common` utilities such as `dump`, `load`, and `Icon`.
  - Update `shelter_map/by_city/__init__.py` so the city is included in `all_cities`.
  - Document the new city in the README's feature list.

## Submitting changes

- Run `pre-commit install` before committing any code.
- Try to keep the code style and naming consistent with existing code.
- It's a good idea to run your code through an AI agent for clean-ups and consistency check.
- By contributing, you agree that your work will be released under the MIT License.

Thanks for contributing!
