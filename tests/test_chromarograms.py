# 3rd party
from libgunshotmatch.project import Project
from matplotlib import pyplot as plt

# this package
from common import check_images
from libgunshotmatch_mpl.chromatogram import draw_chromatograms


@check_images
def test_draw_chromatograms(hymax_project: Project):

	fig = plt.figure(layout="constrained", figsize=(11.7, 8.3))
	axes = fig.subplots(len(hymax_project.datafile_data), 1, sharex=True)
	draw_chromatograms(hymax_project, fig, axes)

	return fig
