#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:

"""

import logging

__pgmname__ = 'hold'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)


class hold(object):
	def __init__(self, id=None, **kwargs):
		log.trace('hold.__init__')
		super(hold, self).__init__()

	@property
	def Seasons(self):
		"""The series season data"""
		return self._seasons
	@Seasons.setter
	def Seasons(self, value):
		try:
			_seasons = getSeasons(self.trakt_id, rtn=str)
		except:
			_seasons = None

		if _seasons:
			self._seasons = {}
			for _entry in _seasons:
				self._seasons['<Season {0:02}>'.format(_entry['number'])] = Season(self.trakt_id, **_entry)

	def Season(self, number=1):
		if '<Season {0:02}>'.format(number) in self.seasons:
			return self.seasons['<Season {0:02}>'.format(number)]
		else:
			raise SeasonNotFound('SeasonNotFound: {} - Season {}'.format(self.titleTVDB, number))

	def Episode(self, snumber, number):
		_eplist = []
		_season = self.season(snumber)
		if _season:
			for _entry in number:
				if _entry > 0 and not _entry > len(_season.episodes):
					_eplist.append(_season.episodes['E{0:02d}'.format(_entry)])
		else:
			raise SeasonNotFound('SeasonNotFound: {} - Season {}'.format(self.titleTVDB, snumber))
		if _eplist:
			return _eplist
		else:
			raise EpisodeNotFound('EpisodeNotFound: {} - Season {}  Episode {}'.format(self.titleTVDB,
																					   snumber,
																					   number))


if __name__ == '__main__':

	from sys import argv
	from dadvision import DadVision
	from logging import DEBUG;

	TRACE = 5;
	VERBOSE = 15
	DadVision.logger.initialize(level=DEBUG)

	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])
	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
