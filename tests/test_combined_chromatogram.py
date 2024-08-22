# 3rd party
import matplotlib  # type: ignore[import]
import pytest
from libgunshotmatch.project import Project
from matplotlib import pyplot as plt
from matplotlib.colors import Colormap  # type: ignore[import]

# this package
from common import check_images
from libgunshotmatch_mpl.chromatogram import annotate_peaks, draw_combined_chromatogram


@check_images
def test_combined_chromatogram_mean_areas(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			)
	return fig


@check_images
def test_combined_chromatogram_annotate(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			)
	annotate_peaks(hymax_project, fig, ax, top_n_peaks=10)
	return fig


@check_images
def test_combined_chromatogram_threshold(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			minimum_area=1_000_000_000,
			)
	return fig


@check_images
def test_combined_chromatogram_points(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			show_points=True,
			)
	return fig


@check_images
def test_combined_chromatogram_median_areas(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(hymax_project, fig, ax, top_n_peaks=40, use_median=True)
	return fig


@check_images
def test_combined_chromatogram_median_height(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			use_median=True,
			use_peak_height=True,
			)
	return fig


@check_images
def test_combined_chromatogram_mean_height(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			use_peak_height=True,
			)
	return fig


@check_images
def test_combined_chromatogram_mean_range(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(hymax_project, fig, ax, top_n_peaks=40, use_range=True)
	return fig


@check_images
@pytest.mark.parametrize(
		"colourmap", [
				pytest.param(matplotlib.cm.gist_ncar, id="gist_ncar"),
				pytest.param(matplotlib.cm.prism, id="prism"),
				]
		)
def test_combined_chromatogram_colourmap(hymax_project: Project, colourmap: Colormap):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			hymax_project,
			fig,
			ax,
			top_n_peaks=40,
			colourmap=colourmap,
			)
	return fig


@check_images
def test_combined_chromatogram_error_bars():
	unknown = Project.from_file("tests/Eley Hymax 1.gsmp")

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	ax = fig.subplots(1, 1, sharex=True)
	# print(min(peak.area for peak in project.consolidated_peaks))

	draw_combined_chromatogram(
			unknown,
			fig,
			ax,
			top_n_peaks=40,
			)
	return fig
