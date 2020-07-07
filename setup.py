from setuptools import setup

setup(
    name="aml",
    version="0.0.001",
    license="GPL",
    description="aml is a composition for a piano quartet & tape",
    author="Levin Eric Zimmermann",
    author_email="levin-eric.zimmermann@folkwang-uni.de",
    url="https://github.com/levinericzimmermann/aml",
    packages=[
        "aml",
        "aml.breads",
        "aml.chapters",
        "aml.comprovisation",
        "aml.complex_meteres",
        "aml.globals_",
        "aml.transcriptions",
        "aml.versmaker",
        "aml.trackmaker",
        "aml.transcriptions",
        # "aml.fragments",
        # "aml.parts",
        # "aml.segments",
    ],
    package_data={},
    include_package_data=True,
    setup_requires=[""],
    tests_require=["nose"],
    install_requires=[""],
    extras_require={},
    python_requires=">=3.6",
)