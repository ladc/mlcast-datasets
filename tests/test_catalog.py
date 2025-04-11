from pathlib import Path

import intake
import pytest
from loguru import logger
from sh import git


def root_path():
    return Path(__file__).parent.parent


def get_master_catalog():
    p_catalog = root_path() / "catalog.yml"
    assert p_catalog.exists()
    return intake.open_catalog(str(p_catalog))


@pytest.fixture
def catalog():
    return get_master_catalog()


def all_entries(reference_branch="origin/main"):
    relevant_files = set(
        line.strip()
        # for l in git.log("--oneline", "--name-only",
        # f"{reference_branch}...HEAD", _tty_out=False, _iter=True))
        # for now we just check all catalog.yml files
        for line in git.log(
            "--oneline", "--name-only", "**/catalog.yml", _tty_out=False, _iter=True
        )
    )

    root = root_path()
    relevant_files = set(root / f for f in relevant_files if (root / f).exists())

    catalog = get_master_catalog()

    def marks_for(e):
        if Path(catalog[e].catalog_object.path) in relevant_files:
            yield pytest.mark.modified_on_branch

    return [
        pytest.param(e, marks=list(marks_for(e)))
        for e in get_master_catalog().walk(depth=10)
    ]


@pytest.mark.parametrize("dataset_name", all_entries())
def test_get_intake_source(catalog, dataset_name):
    item = catalog[dataset_name]
    logger.debug(f"Testing {item}")
    if item.container == "catalog":
        item.reload()
    else:
        print(f"Testing {item}")
        plugin = item.cat.describe()["plugin"][0]
        if plugin in ["opendap", "zarr", "netcdf"]:
            _ = item.to_dask()
        elif plugin in ["intake_esm.esm_datastore", "parquet"]:
            _ = item.get()
        elif plugin in ["json"]:
            _ = item.read()
        elif plugin == "yaml_file_cat":
            pass
        else:
            raise Exception(plugin)


@pytest.mark.modified_on_branch
def test_make_ci_happy_if_no_test_is_selected():
    """pytest returns exit code 5 if no test is selected"""
    pass
