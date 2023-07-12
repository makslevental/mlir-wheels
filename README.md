# MLIR distribution as (`manylinux`-compatible) wheel

What's this? It's a means to getting a distribution of MLIR like this:

```shell
$ pip install mlir -f https://github.com/makslevental/cibuildwheel-llvm-mlir/releases/expanded_assets/latest
```

This will install a thing that will let you do this:

```python
import mlir
print(mlir.__path__[0])
>>> /home/mlevental/mambaforge/envs/nelli/lib/python3.11/site-packages/mlir
```

where `site-packages/mlir` looks like this:

```shell
$ tree -L 1 site-packages/mlir
site-packages/mlir
├── bin
├── include
├── lib
├── python_packages
├── share
└── src
```

i.e., a full distribution of MLIR (and LLVM).
What's the point of distributing a primarily binary distribution as a python wheel?

1. By building using `cibuildwheel`, it's guaranteed that the distro is `manylinux` compatible, and thus can be used a foundation for other `manylinux` compatible python wheels.
2. Using `--extra-index-url` or `--find-links`, you can include these wheels as a dependency in your requirements.txt, like so:
   ```text
   -f https://github.com/makslevental/cibuildwheel-llvm-mlir/releases/expanded_assets/latest
   mlir==17.0.0+6c7fd723
   ```
   i.e., [releases/expanded_assets/latest](https://github.com/makslevental/cibuildwheel-llvm-mlir/releases/expanded_assets/latest) works as a suitable package index.

# Versioning

I'm abusing the hell out of [PEP 440](https://peps.python.org/pep-0440/) compatible version strings with things like this:

```shell
mlir-17.0.0+4a63264d-cp311-cp311-macosx_11_0_arm64.whl
mlir-17.0.0+4a63264d.vulkan.openmp-cp311-cp311-macosx_11_0_arm64.whl
mlir-17.0.0+f3059e22.cuda.vulkan.openmp-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

Anyway the point is, if you want to pin to a particular llvm commit hash then you need to specify in your `requirements.txt` the full version string (everything up until the platform `cp311` stuff starts).

# Archs

[Currently](https://github.com/makslevental/cibuildwheel-llvm-mlir/blob/main/.github/workflows/wheels.yml#L68-L94), there are wheels for {(`x86_64`, `aarch64/arm64/ARM64`) ⨯ (`linux`, `mac`, `windows`)} - {(`linux`, `aarch64`), (`windows`, `ARM64`)}, i.e., arm builds of both linux and windows don't work yet.
It's on my todo list but both of these suck for their own distinct reasons so who knows 🤷.

# Build frequency

This repo cuts a new build at `'00 01,07,13,19 * * *'`, i.e., at minute 0 past hour 1, 7, 13, and 19 of every day (see https://crontab.guru).
All of the artifacts are uploaded to the [`latest` tag](https://github.com/makslevental/cibuildwheel-llvm-mlir/releases/tag/latest) release page.
If you want some commit that's not there just open an issue and I'll kick off a build.
