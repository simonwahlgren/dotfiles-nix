---
name: migrate-nix-poetry-shell
description: Migrate a shell.nix that builds poetry plugins (pkgs.poetry.withPlugins with buildPythonPackage) to nixpkgs 25.11+. Use when such a shell fails after a nixpkgs upgrade with "does not configure a 'format'", a Python version mismatch between poetry and a plugin, or "<package> not installed". Not for shell.nix files without poetry.
---

# Migrate Poetry shell.nix to NixOS 25.11+

Skill for migrating `shell.nix` files that use `pkgs.poetry` with custom Python plugins (e.g., `keyrings.google-artifactregistry-auth`) to be compatible with NixOS 25.11+.

## When to use

When a `shell.nix` that uses `pkgs.poetry.withPlugins` fails after upgrading NixOS/nixpkgs with errors like:
- `does not configure a 'format'. To build with setuptools as before, set 'pyproject = true' and 'build-system = [ setuptools ]'`
- `Python version mismatch` between poetry and a plugin package

This skill is specifically for shell.nix files that combine a project Python (e.g., python312) with poetry and custom poetry plugins built via `buildPythonPackage`. It does NOT apply to shell.nix files without poetry.

## Migration steps

### 1. Build poetry plugins with poetry's Python, not the project Python

In NixOS 25.11, `pkgs.poetry` uses Python 3.13. If you build a plugin with a different Python (e.g., `python312.pkgs`), you get a version mismatch. Extract poetry's package set and use it for the plugin:

```nix
# Before
python = pkgs.python312;
myPlugin = python.pkgs.buildPythonPackage { ... };
poetryWithPlugins = pkgs.poetry.withPlugins (_: [ myPlugin ]);

# After
python = pkgs.python312;
poetryPython = pkgs.poetry.python.pkgs;
myPlugin = poetryPython.buildPythonPackage { ... };
poetryWithPlugins = pkgs.poetry.withPlugins (_: [ myPlugin ]);
```

All `dependencies` and `build-system` references in the plugin must also use `poetryPython`, not the project's Python.

### 2. Add `pyproject = true` to plugin `buildPythonPackage` calls

```nix
# Before
poetryPython.buildPythonPackage rec {
  pname = "...";
  version = "...";
  ...
};

# After
poetryPython.buildPythonPackage rec {
  pname = "...";
  version = "...";
  pyproject = true;
  ...
};
```

### 3. Rename `propagatedBuildInputs` to `dependencies`

```nix
# Before
propagatedBuildInputs = with poetryPython; [ keyring google-auth ];

# After
dependencies = with poetryPython; [ keyring google-auth ];
```

### 4. Rename `nativeBuildInputs` to `build-system`, drop `pip` and `wheel`

```nix
# Before
nativeBuildInputs = with poetryPython; [ pip wheel setuptools setuptools-scm ];

# After
build-system = with poetryPython; [ setuptools setuptools-scm ];
```

### 5. Fix missing runtime dependencies

NixOS 25.11 has stricter runtime dep checking. If the build fails with `<package> not installed`, add it to `dependencies`. Common example:

```nix
dependencies = with poetryPython; [
  keyring
  google-auth
  google-auth-oauthlib
  pluggy  # often missing - needed by plugin systems
];
```

## Validation

After applying all changes, run `direnv reload` in the project directory and verify:
- No `error:` lines in the output
- No `Falling back to previous environment` message
- The shell loads successfully with the expected tools available

If `direnv reload` still fails, check the error message:
- `does not configure a 'format'` — a `buildPythonPackage` is still missing `pyproject = true`
- `Python version mismatch` — a plugin is still being built with the wrong Python
- `<package> not installed` — a runtime dependency is missing from `dependencies`

Fix the reported issue and run `direnv reload` again until it succeeds.

## Quick checklist

- [ ] Plugin built with `pkgs.poetry.python.pkgs`, not project Python
- [ ] `pyproject = true` added to plugin's `buildPythonPackage`
- [ ] `propagatedBuildInputs` renamed to `dependencies`
- [ ] `nativeBuildInputs` (build tools) renamed to `build-system`
- [ ] `pip` and `wheel` removed from `build-system`
- [ ] All runtime deps satisfied (check build logs for `not installed` errors)
- [ ] Project Python (e.g., `python312`) left unchanged in `mkShell.packages`
- [ ] `direnv reload` completes without errors
