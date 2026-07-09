# Archetype integration tests

This archetype is tested by the shared
[archetype-test-harness](https://github.com/p6m-archetypes/archetype-test-harness):
it renders the archetype headlessly with the answers in [answers/](answers/), checks
the generated project (expected files present, no unrendered `{{ placeholder }}`
tokens, generated YAML parses), and builds the generated `uv` workspace. This
directory holds only data - the test code lives in the harness repo.

One `default` case is covered (this archetype has no persistence prompt).

## What the build tier does

`uv sync --python 3.12` resolves and builds the whole generated workspace,
including the gRPC proto codegen in `inventory-service-proto`. It does **not** run
the generated project's tests:

- the shipped unit tests are unimplemented scaffolds (undefined `test_data_factory`
  fixture, commented-out imports); and
- the integration tests require Docker/Postgres.

So the build tier's job here is to prove the generated workspace installs and builds
cleanly. Python 3.12 is pinned because `psycopg2-binary` has no wheels for the
newest interpreters (which would force a slow, toolchain-dependent from-source build).

## Prerequisites

- [archetect](https://archetect.github.io/) **2.x** - this archetype uses a Rhai
  script, which archetect 3.x refuses to render. Install v2 alongside v3:

  ```sh
  brew install archetect/tap/archetect@2
  ln -s /opt/homebrew/opt/archetect@2/bin/archetect /opt/homebrew/bin/archetect2
  ```

  The harness reads `requires.archetect` from [archetype.yaml](../archetype.yaml)
  and looks for `$ARCHETECT2`, then `archetect2` on PATH, then the homebrew keg.
- [uv](https://docs.astral.sh/uv/) on PATH (`brew install uv`) - used both to run
  the harness and as the generated project's package manager for the build tier.
- Network access to GitHub - the archetype composes prompt/manifest components from
  git sources; archetect caches them after the first render.

## Running

From the repo root (or this directory):

```sh
# in the flat org checkout, against the sibling harness:
uvx --from ../archetype-test-harness archetype-test

# anywhere, against the published harness:
uvx --from git+https://github.com/p6m-archetypes/archetype-test-harness@main archetype-test
```

Extra arguments pass through to pytest:

```sh
archetype-test -m "not build"   # fast tier only: render + static checks
archetype-test --offline        # use archetect's cached component sources
archetype-test -v -ra           # verbose, with skip/fail reasons
```

## CI

[.github/workflows/test.yaml](../.github/workflows/test.yaml) calls the harness's
reusable workflow with `archetect-version: 2.1.2` (installed as `archetect2`) on
every push and manual dispatch. The harness always sets up `uv`, so the build tier
runs in CI. On failure it uploads the rendered project as a build artifact.

## Adding a test case

Add an entry to [manifest.yaml](manifest.yaml) plus an answers file under
[answers/](answers/) - the schema is documented in the
[harness README](https://github.com/p6m-archetypes/archetype-test-harness#manifestyaml-schema).
