#!/usr/bin/env python3
#
#  combined_chromatogram.py
"""
Combined "chromatogram" drawing functionality.

A bar chart for peak area/height styled as a chromatogram, with time on the x-axis.

.. versionadded:: 0.5.0
"""
#
#  Copyright © 2023-2024 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
from operator import attrgetter
from typing import List, NamedTuple, Optional, Tuple, Union

# 3rd party
import numpy
from libgunshotmatch.consolidate import ConsolidatedPeak
from libgunshotmatch.project import Project
from libgunshotmatch.utils import get_rt_range
from matplotlib.axes import Axes  # type: ignore[import]
from matplotlib.container import BarContainer  # type: ignore[import]
from matplotlib.figure import Figure  # type: ignore[import]
from matplotlib.ticker import AutoMinorLocator  # type: ignore[import]

__all__ = ("CCPeak", "draw_combined_chromatogram", "get_cc_peak", "get_combined_chromatogram_data")


class CCPeak(NamedTuple):
	"""
	Data for a peak in a combined "chromatogram".
	"""

	area_or_height: float
	area_or_height_list: List[float]
	rt: float
	rt_list: List[float]
	errorbar: Union[float, Tuple[List[float], List[float]]]


def get_cc_peak(
		peak: ConsolidatedPeak,
		use_median: bool = False,
		use_peak_height: bool = False,
		) -> CCPeak:
	"""
	Return data on a peak for a combined "chromatogram".

	:param peak:
	:param use_median: Show the median and inter-quartile range, rather than the mean and standard deviation.
	:param use_peak_height: Show the peak height and not the peak area.
	"""

	if use_peak_height:
		areas = [sum(ms.intensity_list) for ms in peak.ms_list]
	else:
		areas = peak.area_list

	if use_median:
		area: float = numpy.nanmedian(areas)
		_25th_percentile: float = numpy.nanpercentile(areas, 25)
		_75th_percentile: float = numpy.nanpercentile(areas, 75)
		errorbar = ([area - _25th_percentile], [_75th_percentile - area])

		return CCPeak(
				area_or_height=area,
				area_or_height_list=areas,
				rt=peak.rt / 60,
				rt_list=peak.rt_list,
				errorbar=errorbar,
				)
	else:
		return CCPeak(
				area_or_height=numpy.nanmean(areas),
				area_or_height_list=areas,
				rt=peak.rt / 60,
				rt_list=peak.rt_list,
				errorbar=numpy.nanstd(areas),
				)


def get_combined_chromatogram_data(
		project: Project,
		*,
		top_n_peaks: Optional[int] = None,
		threshold: float = 0,
		use_median: bool = False,
		use_peak_height: bool = False,
		) -> List[CCPeak]:
	"""
	Returns data for a combined "chromatogram" for the project.

	:param project:
	:param top_n_peaks: Show only the n largest peaks.
	:param threshold: Show only peaks larger than the given area (or peak height, as applicable).
	:param use_median: Show the median and inter-quartile range, rather than the mean and standard deviation.
	:param use_peak_height: Show the peak height and not the peak area.
	:param show_points: Show individual retention time / peak area scatter points.
	"""

	assert project.consolidated_peaks is not None

	peaks: List[CCPeak] = []
	for peak in project.consolidated_peaks:
		peak_data = get_cc_peak(peak, use_median, use_peak_height)
		if peak_data.area_or_height < threshold:
			continue
		peaks.append(peak_data)

	if top_n_peaks:
		# Sort by peak area and take largest ``top_n_peaks``
		peaks = sorted(peaks, key=attrgetter("area_or_height"), reverse=True)[:top_n_peaks]

		# Resort by retention time
		peaks.sort(key=attrgetter("rt"))

	return peaks


def draw_combined_chromatogram(
		project: Project,
		figure: Figure,
		ax: Axes,
		*,
		top_n_peaks: Optional[int] = None,
		minimum_area: float = 0,
		use_median: bool = False,
		use_peak_height: bool = False,
		show_points: bool = False,
		) -> None:
	"""
	Draw a combined "chromatogram" for the project.

	A bar chart for peak area/height styled as a chromatogram, with time on the x-axis.

	:param project:
	:param figure:
	:param ax:
	:param top_n_peaks: Show only the n largest peaks.
	:param minimum_area: Show only peaks larger than the given area (or peak height, as applicable).
	:param use_median: Show the median and inter-quartile range, rather than the mean and standard deviation.
	:param use_peak_height: Show the peak height and not the peak area.
	:param show_points: Show individual retention time / peak area scatter points.

	:rtype:

	.. versionadded:: 0.2.0
	.. versionchanged:: 0.4.0  Added the ``use_median``, ``use_peak_height`` and ``show_points`` keyword arguments.

	.. versionchanged:: 0.5.0

		* Moved to the :mod:`~.combined_chromatogram` module.
		* Y-axis label now reflects ``use_median`` and ``use_peak_height`` options.
	"""

	# this package
	from libgunshotmatch_mpl.chromatogram import ylabel_sci_1dp

	assert project.consolidated_peaks is not None

	min_rt, max_rt = get_rt_range(project)

	peaks = get_combined_chromatogram_data(
			project,
			top_n_peaks=top_n_peaks,
			threshold=minimum_area,
			use_median=use_median,
			use_peak_height=use_peak_height,
			)

	for peak in peaks:

		bar: BarContainer = ax.bar(peak.rt, peak.area_or_height, width=0.2)
		if show_points:
			bar_colour = bar.patches[0].get_facecolor()  # So they match
			ax.scatter(
					[rt / 60 for rt in peak.rt_list],
					peak.area_or_height_list,
					s=50,
					color=bar_colour,
					marker='x',
					)

		if len(peak) > 1:
			errorbars = ax.errorbar(
					peak.rt, peak.area_or_height, yerr=peak.errorbar, color="darkgrey", capsize=5, clip_on=False
					)

			# for eb in errorbars[1]:
			# 	eb.set_clip_on(False)

	# ylabel_use_sci(ax)
	ax.set_ylim(bottom=0)
	ylabel_sci_1dp(ax)

	if use_peak_height and use_median:
		ax.set_ylabel("Median Peak Height")
	elif use_peak_height:
		ax.set_ylabel("Mean Peak Height")
	elif use_median:
		ax.set_ylabel("Median Peak Area")
	else:
		ax.set_ylabel("Mean Peak Area")

	ax.set_xlim(min_rt, max_rt)
	ax.set_xlabel("Retention Time (mins)")
	ax.xaxis.set_minor_locator(AutoMinorLocator())

	figure.suptitle(project.name)
