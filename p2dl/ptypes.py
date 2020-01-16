from descarteslabs.common.dotdict import DotDict

from enum import Enum

class AssetType(Enum):
    analytic = 1 # Radiometrically calibrated GeoTiff suitable for analytic applications.
    analytic_sr = 2 # Atmospherically corrected surface reflectance product.
    analytic_xml = 3 # Analytic asset XML metadata file.
    analytic_dn = 4  # Non-radiometrically calibrated GeoTiff suitable for analytic applications.
    analytic_dn_xml = 5  # Analytic DN asset XML metadata file.
    udm = 6  # Unusable Data Mask - Unusable data bit mask in GeoTIFF format for the visual and analytic scene assets.
    basic_analytic =  7 # Top of atmosphere radiance (at sensor) and sensor corrected GeoTiff. Scene based framing and not projected to a cartographic projection.
    basic_analytic_xml = 8  # Basic analytic asset XML metadata file.
    basic_analytic_rpc = 9  # Rational Polynomial Coefficients text file used to orthorectify the basic_analytic asset.
    basic_analytic_dn = 10  # Basic sensor corrected scene GeoTiff. Scene based framing and not projected to a cartographic projection.
    basic_analytic_dn_xml = 11  # Basic analytic DN asset XML metadata file.
    basic_analytic_dn_rpc = 12  # Rational Polynomial Coefficients text file used to orthorectify basic_analytic_dn asset.
    basic_analytic_nitf = 13  # Top of atmosphere radiance (at sensor) and sensor corrected in NITF format. Scene based framing and not projected to a cartographic projection.
    basic_analytic_xml_nitf = 14  # Basic analytic XML metadata file.
    basic_analytic_rpc_nitf = 15  # Rational Polynomial Coefficients text file used to orthorectify the basic_analytic asset.
    basic_analytic_dn_nitf = 16  # Basic sensor corrected scene NITF. Scene based framing and not projected to a cartographic projection.
    basic_analytic_dn_xml_nitf = 17  # Basic analytic DN XML metadata file.
    basic_analytic_dn_rpc_nitf = 18  # Rational Polynomial Coefficients text file used to orthorectify basic_analytic_dn_nitf asset.
    basic_udm = 19  # Usable Data Mask - Usable data bit mask in GeoTIFF format for the basic analytic scene assets.
    basic_udm2 = 20  # Usable Data Mask 2.0. Read more about this new asset here.


# Planet item definitions
ItemType = DotDict(
    PSScene4Band = DotDict({
        'id':'pss4band',
        'name': 'PSScene4Band',
        'bundle': AssetType.analytic, 
        'files': ['3B_AnalyticMS_clip.tif','3B_AnalyticMS_DN_udm_clip.tif'],
        'bands': [
            { 'name': 'blue',
              'band_index':0,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral',
              'file_index': 0
            },
            { 'name':'green',
              'band_index':1,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral',
              'file_index': 0
            },
            { 'name':'red',
              'band_index':2,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral',
              'file_index': 0
            },
            { 'name':'nir',
              'band_index':3,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral',
              'file_index': 0
            },
            
            { 'name':'udm',
              'band_index':0,
              'data_range':[0,1],
              'display_range':[0,1],
              'data_type': 'Byte',
              'type': 'spectral',
              'file_index': 1
            }
        ]}),
    PSScene3Band =  DotDict({
        'id':'pss3band',
        'name': 'PSScene3Band',
        'asset_types': [],
        'files': [],
        'bands': [
            { 'name': 'blue',
              'band_index':0,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'green',
              'band_index':1,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red',
              'band_index':2,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            }
        ]}),
    PSOrthoTile = DotDict({
        'id':'psorthotile',
        'name':'PSOrthoTile',
        'asset_types': [],
        'bands': [
            { 'name': 'blue',
              'band_index':0,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'green',
              'band_index':1,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red',
              'band_index':2,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            }
        ]}),
    REScene = DotDict({
        'id':'rescene',
        'bands': [
            { 'name': 'blue',
              'band_index':0,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'green',
              'band_index':1,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red',
              'band_index':2,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red-edge',
              'band_index':3,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'nir',
              'band_index':3,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            }
        ]}),
    REOrthoTile = DotDict({
        'id':'reorthtile',
        'bands': [
            { 'name': 'blue',
              'band_index':0,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'green',
              'band_index':1,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red',
              'band_index':2,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'red-edge',
              'band_index':3,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            },
            { 'name':'nir',
              'band_index':3,
              'data_range':[0,10000],
              'display_range':[0,4000],
              'data_type': 'UInt16',
              'type': 'spectral'
            }
        ]}))