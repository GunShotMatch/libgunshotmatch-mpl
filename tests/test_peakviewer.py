# 3rd party
import pytest
from libgunshotmatch.project import Project
from matplotlib import pyplot as plt

# this package
from common import check_images
from libgunshotmatch_mpl.peakviewer import draw_peaks, load_project


def test_load_project():
	load_project("tests/Eley Hymax.gsmp")


@pytest.mark.parametrize("peak_idx", range(76))
@check_images
def test_draw_peaks(hymax_project: Project, peak_idx: int):

	figure = plt.figure(figsize=(10.5, 5), layout="constrained")
	axes = figure.subplots(
			len(hymax_project.datafile_data),
			1,
			sharex=True,
			)

	assert hymax_project.consolidated_peaks is not None
	draw_peaks(hymax_project, hymax_project.consolidated_peaks[peak_idx].rt_list, figure, axes)

	return figure
