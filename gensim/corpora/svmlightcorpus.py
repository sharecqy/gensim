#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Radim Rehurek <radimrehurek@seznam.cz>
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html


"""
Corpus in SVMlight format.
"""


from __future__ import with_statement

import logging

from gensim import interfaces, utils
from gensim.corpora import IndexedCorpus


logger = logging.getLogger('gensim.corpora.svmlightcorpus')


class SvmLightCorpus(IndexedCorpus):
    """
    Corpus in SVMlight format.

    Quoting http://svmlight.joachims.org/:
    The input file contains the training examples. The first lines
    may contain comments and are ignored if they start with #. Each of the following
    lines represents one training example and is of the following format::

        <line> .=. <target> <feature>:<value> <feature>:<value> ... <feature>:<value> # <info>
        <target> .=. +1 | -1 | 0 | <float>
        <feature> .=. <integer> | "qid"
        <value> .=. <float>
        <info> .=. <string>

    The "qid" feature (used for SVMlight ranking), if present, is ignored.

    Although not mentioned in the specification above, SVMlight also expect its
    feature ids to be 1-based (counting starts at 1). We convert features to 0-base
    internally by decrementing all ids when loading a SVMlight input file, and
    increment them again when saving as SVMlight.
    """

    def __init__(self, fname):
        """
        Initialize the corpus from a file.
        """
        IndexedCorpus.__init__(self, fname)
        logger.info("loading corpus from %s" % fname)

        self.fname = fname # input file, see class doc for format
        self.length = None


    def __iter__(self):
        """
        Iterate over the corpus, returning one sparse vector at a time.
        """
        length = 0
        with open(self.fname) as fin:
            for lineNo, line in enumerate(fin):
                doc = self.line2doc(line)
                if doc is not None:
                    length += 1
                    yield doc
        self.length = length


    @staticmethod
    def save_corpus(fname, corpus, id2word=None, labels=False):
        """
        Save a corpus in the SVMlight format.

        The SVMlight `<target>` class tag is set to 0 for all documents.

        This function is automatically called by `SvmLightCorpus.serialize`; don't
        call it directly, call `serialize` instead.
        """
        logger.info("converting corpus to SVMlight format: %s" % fname)
        
        offsets = []
        with open(fname, 'w') as fout:
            for docno, doc in enumerate(corpus):
                label = labels[docno] if labels else 0 # target class is 0 by default
                offsets.append(fout.tell())
                fout.write(SvmLightCorpus.doc2line(doc, label))
        return offsets


    def docbyoffset(self, offset):
        """
        Return the document stored at file position `offset`.
        """
        with open(self.fname) as f:
            f.seek(offset)
            return self.line2doc(f.readline())


    def line2doc(self, line):
        line = line[: line.find('#')].strip()
        if not line:
            return None # ignore comments and empty lines
        parts = line.split()
        if not parts:
            raise ValueError('invalid format at line no. %i in %s' %
                             (lineNo, self.fname))
        target, fields = parts[0], [part.rsplit(':', 1) for part in parts[1:]]
        doc = [(int(p1) - 1, float(p2)) for p1, p2 in fields if p1 != 'qid'] # ignore 'qid' features, convert 1-based feature ids to 0-based
        return doc


    @staticmethod
    def doc2line(doc, label=0):
        pairs = ' '.join("%i:%s" % (termid + 1, termval) for termid, termval in doc) # +1 to convert 0-base to 1-base
        return str(label) + " %s\n" % pairs
#endclass SvmLightCorpus

