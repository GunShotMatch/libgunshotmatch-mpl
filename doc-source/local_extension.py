# Adapted from https://github.com/sphinx-doc/sphinx/blob/master/sphinx/environment/adapters/toctree.py
#
# Copyright (c) 2007-2021 by the Sphinx team.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# stdlib
from typing import Any, Iterable, List, cast

# 3rd party
from docutils import nodes
from docutils.nodes import Element, Node
from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.environment import BuildEnvironment
from sphinx.environment.adapters.toctree import TocTree, logger
from sphinx.locale import __
from sphinx.util import logging, url_re
from sphinx.util.matching import Matcher
from sphinx.util.nodes import clean_astext, process_only_nodes


def resolve(
		self,
		docname: str,
		builder: Builder,
		toctree: addnodes.toctree,
		prune: bool = True,
		maxdepth: int = 0,
		titles_only: bool = False,
		collapse: bool = False,
		includehidden: bool = False
		) -> Element:
	"""Resolve a *toctree* node into individual bullet lists with titles
	as items, returning None (if no containing titles are found) or
	a new node.

	If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
	to the value of the *maxdepth* option on the *toctree* node.
	If *titles_only* is True, only toplevel document titles will be in the
	resulting tree.
	If *collapse* is True, all branches not containing docname will
	be collapsed.
	"""
	if toctree.get("hidden", False) and not includehidden:
		return None

	# For reading the following two helper function, it is useful to keep
	# in mind the node structure of a toctree (using HTML-like node names
	# for brevity):
	#
	# <ul>
	#   <li>
	#     <p><a></p>
	#     <p><a></p>
	#     ...
	#     <ul>
	#       ...
	#     </ul>
	#   </li>
	# </ul>
	#
	# The transformation is made in two passes in order to avoid
	# interactions between marking and pruning the tree (see bug #1046).

	toctree_ancestors = self.get_toctree_ancestors(docname)
	excluded = Matcher(self.env.config.exclude_patterns)

	def _toctree_add_classes(node: Element, depth: int) -> None:
		"""Add 'toctree-l%d' and 'current' classes to the toctree."""
		for subnode in node.children:
			if isinstance(subnode, (addnodes.compact_paragraph, nodes.list_item)):
				# for <p> and <li>, indicate the depth level and recurse
				subnode["classes"].append("toctree-l%d" % (depth - 1))
				_toctree_add_classes(subnode, depth)
			elif isinstance(subnode, nodes.bullet_list):
				# for <ul>, just recurse
				_toctree_add_classes(subnode, depth + 1)
			elif isinstance(subnode, nodes.reference):
				# for <a>, identify which entries point to the current
				# document and therefore may not be collapsed
				if subnode["refuri"] == docname:
					if not subnode["anchorname"]:
						# give the whole branch a 'current' class
						# (useful for styling it differently)
						branchnode = subnode  # type: Element
						while branchnode:
							branchnode["classes"].append("current")
							branchnode = branchnode.parent
					# mark the list_item as "on current page"
					if subnode.parent.parent.get("iscurrent"):
						# but only if it's not already done
						return
					while subnode:
						subnode["iscurrent"] = True
						subnode = subnode.parent

	def _entries_from_toctree(
			toctreenode: addnodes.toctree,
			parents: List[str],
			separate: bool = False,
			subtree: bool = False
			) -> List[Element]:
		"""Return TOC entries for a toctree node."""
		refs = [(e[0], e[1]) for e in toctreenode["entries"]]
		entries = []  # type: List[Element]
		for (title, ref) in refs:
			try:
				refdoc = None
				if url_re.match(ref):
					if title is None:
						title = ref
					reference = nodes.reference(
							'', '', internal=False, refuri=ref, anchorname='', *[nodes.Text(title)]
							)
					para = addnodes.compact_paragraph('', '', reference)
					item = nodes.list_item('', para)
					toc = nodes.bullet_list('', item)
				elif ref == "self":
					# 'self' refers to the document from which this
					# toctree originates
					ref = toctreenode["parent"]
					if not title:
						title = clean_astext(self.env.titles[ref])
					reference = nodes.reference(
							'', '', internal=True, refuri=ref, anchorname='', *[nodes.Text(title)]
							)
					para = addnodes.compact_paragraph('', '', reference)
					item = nodes.list_item('', para)
					# don't show subitems
					toc = nodes.bullet_list('', item)
				else:
					if ref in parents:
						logger.warning(
								__('circular toctree references '
									'detected, ignoring: %s <- %s'),
								ref,
								" <- ".join(parents),
								location=ref,
								type="toc",
								subtype="circular"
								)
						continue
					refdoc = ref
					toc = self.env.tocs[ref].deepcopy()
					maxdepth = self.env.metadata[ref].get("tocdepth", 0)
					if ref not in toctree_ancestors or (prune and maxdepth > 0):
						self._toctree_prune(toc, 2, maxdepth, collapse)
					process_only_nodes(toc, builder.tags)
					if title and toc.children and len(toc.children) == 1:
						child = toc.children[0]
						for refnode in child.traverse(nodes.reference):
							# Changes from here
							if refnode["refuri"] == ref:
								if not refnode["anchorname"]:
									if title.startswith("``") and title.endswith("``"):
										refnode.children = [nodes.literal(title, '', nodes.Text(title[2:-2]))]
									else:
										refnode.children = [nodes.Text(title)]
									# To here
				if not toc.children:
					# empty toc means: no titles will show up in the toctree
					logger.warning(
							__(
									'toctree contains reference to document %r that '
									'doesn\'t have a title: no link will be generated'
									),
							ref,
							location=toctreenode
							)
			except KeyError:
				# this is raised if the included file does not exist
				if excluded(self.env.doc2path(ref, None)):
					message = __("toctree contains reference to excluded document %r")
				else:
					message = __("toctree contains reference to nonexisting document %r")

				logger.warning(message, ref, location=toctreenode)
			else:
				# if titles_only is given, only keep the main title and
				# sub-toctrees
				if titles_only:
					# children of toc are:
					# - list_item + compact_paragraph + (reference and subtoc)
					# - only + subtoc
					# - toctree
					children = cast(Iterable[nodes.Element], toc)

					# delete everything but the toplevel title(s)
					# and toctrees
					for toplevel in children:
						# nodes with length 1 don't have any children anyway
						if len(toplevel) > 1:
							subtrees = toplevel.traverse(addnodes.toctree)
							if subtrees:
								toplevel[1][:] = subtrees  # type: ignore
							else:
								toplevel.pop(1)
				# resolve all sub-toctrees
				for subtocnode in toc.traverse(addnodes.toctree):
					if not (subtocnode.get("hidden", False) and not includehidden):
						i = subtocnode.parent.index(subtocnode) + 1
						for entry in _entries_from_toctree(subtocnode, [refdoc] + parents, subtree=True):
							subtocnode.parent.insert(i, entry)
							i += 1
						subtocnode.parent.remove(subtocnode)
				if separate:
					entries.append(toc)
				else:
					children = cast(Iterable[nodes.Element], toc)
					entries.extend(children)
		if not subtree and not separate:
			ret = nodes.bullet_list()
			ret += entries
			return [ret]
		return entries

	maxdepth = maxdepth or toctree.get("maxdepth", -1)
	if not titles_only and toctree.get("titlesonly", False):
		titles_only = True
	if not includehidden and toctree.get("includehidden", False):
		includehidden = True

	# NOTE: previously, this was separate=True, but that leads to artificial
	# separation when two or more toctree entries form a logical unit, so
	# separating mode is no longer used -- it's kept here for history's sake
	tocentries = _entries_from_toctree(toctree, [], separate=False)
	if not tocentries:
		return None

	newnode = addnodes.compact_paragraph('', '')
	caption = toctree.attributes.get("caption")
	if caption:
		caption_node = nodes.title(caption, '', *[nodes.Text(caption)])
		caption_node.line = toctree.line
		caption_node.source = toctree.source
		caption_node.rawsource = toctree["rawcaption"]
		if hasattr(toctree, "uid"):
			# move uid to caption_node to translate it
			caption_node.uid = toctree.uid  # type: ignore
			del toctree.uid  # type: ignore
		newnode += caption_node
	newnode.extend(tocentries)
	newnode["toctree"] = True

	# prune the tree to maxdepth, also set toc depth and current classes
	_toctree_add_classes(newnode, 1)
	self._toctree_prune(newnode, 1, maxdepth if prune else 0, collapse)

	if isinstance(newnode[-1], nodes.Element) and len(newnode[-1]) == 0:  # No titles found
		return None

	# set the target paths in the toctrees (they are not known at TOC
	# generation time)
	for refnode in newnode.traverse(nodes.reference):
		if not url_re.match(refnode["refuri"]):
			refnode["refuri"] = builder.get_relative_uri(docname, refnode["refuri"]) + refnode["anchorname"]
	return newnode


def setup(app):
	TocTree.resolve = resolve
