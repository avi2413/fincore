import os

from setuptools import setup
from setuptools_rust import Binding, RustExtension


os.environ.setdefault("PYO3_USE_ABI3_FORWARD_COMPATIBILITY", "1")

setup(
    rust_extensions=[
        RustExtension(
            "fincore._fincore",
            path="Cargo.toml",
            binding=Binding.PyO3,
        )
    ],
    zip_safe=False,
)
