import xmltodict
import numpy as np
from PIL import Image
import os
import collections

from .obj import RasterSet, Band, SetProperties

class RasterSetReader(object):
    """Read a series of raster files via their XML metadata file in ESPA schema"""

    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename', None)

    @staticmethod
    def ReadTif(tifFile):
        """Reads a tif file to a 2D NumPy array"""
        img = Image.open(tifFile)
        img = np.array(img)
        return img

    @staticmethod
    def CleanDict(d):
        d = {key.replace('@', '').replace('#', ''): item for key, item in d.items()}
        for key, item in d.items():
            if isinstance(item, (collections.OrderedDict, dict)):
                d[key] = RasterSetReader.CleanDict(item)
            elif isinstance(item, list):
                for i in range(len(item)):
                    if isinstance(item[i], (collections.OrderedDict, dict)):
                        item[i] = RasterSetReader.CleanDict(item[i])
        return d


    def GenerateBand(self, band):
        """Genreate a Band object given band metadata

        Args:
            band (dict): dictionary containing metadata for a given band

        Return:
            Band : the loaded Band onject"""

        # Read the band data and add it to dictionary
        fname = band.get('file_name')
        data = self.ReadTif('%s/%s' % (os.path.dirname(self.filename), fname))
        band['data'] = data

        def FixBitmap(d):
            p = d.get('bitmap_description')
            if p:
                lis = p.get('bit')
                bm = dict()
                # Fix bitmap_description from list of dicts to one dict
                for i in lis:
                    key = i['num']
                    value = i['text']
                    bm[key] = value
                del d['bitmap_description']
                d['bitmap_description'] = bm
            return d

        band = SetProperties(Band, FixBitmap(self.CleanDict(band)))
        print(band.name) # TODO: remove
        band.validate()

        return band


    def Read(self):
        """Read the ESPA XML metadata file"""
        meta = xmltodict.parse(
                open(self.filename, 'r').read()
            ).get('espa_metadata')

        # Handle bands seperately
        bands = meta.get('bands').get('band')
        del(meta['bands'])

        if not isinstance(bands, (list)):
            bands = [bands]
        bdict = dict()
        for i in range(len(bands)):
            b = self.GenerateBand(bands[i])
            bdict[b.name] = b
        meta = self.CleanDict(meta)

        # Get spatial refernce
        ras = SetProperties(RasterSet, meta)
        ras.bands = bdict
        ras.validate()

        return ras