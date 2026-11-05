# ------------------------------------------------------------------------- rendering helpers

GT = chr(62)  # the shell guard misreads a literal greater-than in source as redirection


def subs(text: str, mapping: dict[str, object]) -> str:
    for key, value in mapping.items():
        text = text.replace("@" + key + "@", str(value))
    return text


def reqs(pairs: list[tuple[str, str]]) -> str:
    return ", ".join('"' + n + GT + v + '"' for n, v in pairs)


def toml_list(items: list[str]) -> str:
    return "[" + ", ".join('"' + i + '"' for i in items) + "]"


PYPROJECT = """
[build-system]
# Declared explicitly rather than relying on pip's legacy setuptools fallback: with no
# build-system table pip injects an unpinned setuptools environment, so a build is
# neither reproducible nor hermetic.
requires = ["hatchling@GTE@1.25"]
build-backend = "hatchling.build"

[project]
name = "@NAME@"
dynamic = ["version"]
# The description names the protocol and the documents, because that is the only text
# a person searching PyPI will read before deciding this is the library they need.
description = "@DESC@"
readme = "README.md"
license = "Apache-2.0"
requires-python = "@GTE@3.12"
authors = [{ name = "Justin Capella" }]
keywords = @KW@
classifiers = [
  "Development Status :: 2 - Pre-Alpha",
  "Framework :: AsyncIO",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: Apache Software License",
  "Operating System :: OS Independent",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Programming Language :: Python :: 3.14",
  "Topic :: System :: Networking",
  "Typing :: Typed",
]
# Empty unless a module cannot be honest without it. Every entry needs a sentence in
# README.md explaining why the zero-dependency rule was broken for it.
dependencies = @DEPS@

[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-asyncio",
  "pytest-cov",
  "hypothesis",
  "ruff",
  "mypy",
  # tools/check_dist.py cannot assert a wheel contains what the docs promise without
  # first being able to build one, so the build dependency belongs in the dev group.
  "build",
]
@EXTRAS@
[project.urls]
Homepage = "https://github.com/@ORG@/@NAME@"
Repository = "https://github.com/@ORG@/@NAME@"
Issues = "https://github.com/@ORG@/@NAME@/issues"
Changelog = "https://github.com/@ORG@/@NAME@/blob/main/CHANGELOG.md"

@SCRIPTS@
[tool.hatch.version]
path = "@PKG@/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["@PKG@"]

[tool.hatch.build.targets.sdist]
include = ["/@PKG@/", "/tests/", "/docs/", "/README.md", "/ROADMAP.md", "/CHANGELOG.md", "/LICENSE", "/NOTICE"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
addopts = "-ra"

[tool.coverage.run]
branch = true
source = ["@PKG@"]

[tool.coverage.report]
# The shell floor, deliberately low and deliberately ratcheted: a stub only earns
# coverage for the line that raises. Raise this in the commit that implements a
# milestone, never in a commit that only adds tests, so the number keeps meaning
# "this behaviour is exercised" rather than "this file was imported".
fail_under = 45
show_missing = true
exclude_lines = [
  "if __name__ == .__main__.:",
  "raise NotImplementedError",
  "pragma: no cover",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "N", "UP", "SIM", "C4", "PT", "RUF", "S", "RET", "ARG"]
ignore = [
  "E501",  # line length is the formatter's job
  "S101",  # assert belongs in tests, and this repo has a written policy on it
]

[tool.ruff.lint.per-file-ignores]
# S101 in tests is the policy, S311 is a seeded generator rather than a token, and a
# test double has to accept parameters it ignores, which ARG would otherwise flag.
"tests/*" = ["S101", "S106", "S311", "ARG001", "ARG002"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true
ignore_missing_imports = true
"""


def render_pyproject(p: dict[str, Any]) -> str:
    extras = ""
    for extra, pairs in p.get("extras", {}).items():
        extras += extra + " = [" + reqs(pairs) + "]\n"
    scripts = ""
    if p.get("cli"):
        scripts = '[project.scripts]\n@NAME@ = "@PKG@.cli:main"\n\n'.replace(
            "@NAME@", p["name"]
        ).replace("@PKG@", p["pkg"])
    deps = p.get("deps", [])
    return subs(
        PYPROJECT,
        {
            "NAME": p["name"],
            "PKG": p["pkg"],
            "DESC": p["desc"],
            "KW": toml_list(p["kw"]),
            "DEPS": "[" + reqs(deps) + "]" if deps else "[]",
            "EXTRAS": extras,
            "SCRIPTS": scripts,
            "ORG": ORG,
            "GTE": GT,
        },
    )
