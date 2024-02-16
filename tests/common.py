# 3rd party
import pytest
from domdf_python_tools.paths import PathPlus

baseline_dir = str(PathPlus(__file__).parent / "baseline")
image_hashes = str(PathPlus(__file__).parent / "image_hashes.json")

check_images = pytest.mark.mpl_image_compare(
		baseline_dir=baseline_dir,
		savefig_kwargs={"dpi": 600},
		hash_library=image_hashes,
		)
