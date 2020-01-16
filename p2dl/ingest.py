from planet.api import ClientV1
import planet.api as p
import descarteslabs as dl
import os, sys
from descarteslabs.exceptions import NotFoundError
from tempfile import NamedTemporaryFile
import time
import json
import requests
import pathlib
from requests.auth import HTTPBasicAuth
from retrying import retry
import xmltodict

from p2dl.ptypes import AssetType, ItemType


# functions for submitting, polling, and downloading an order
@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def place_order(request, auth):
    orders_url = 'https://api.planet.com/compute/ops/orders/v2'
    headers = {'content-type': 'application/json'}
    print('Placing order to Planet.')
    response = requests.post(orders_url, data=json.dumps(request), auth=auth, headers=headers)
    
    if not response.ok:
        raise Exception(response.content)

    order_id = response.json()['id']
    print(f'Created order: {order_id}')
    order_url = orders_url + '/' + order_id
    return order_url

@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def poll_for_success(order_url, auth, num_loops=50):
    
    for count in range(num_loops):
        r = requests.get(order_url, auth=auth)
        response = r.json()
        state = response['state']
        sys.stdout.write(f'\rOrder {state.ljust(10+count,".")}' )
        
        success_states = ['success', 'partial']
        if state == 'failed':
            raise Exception(response)
        elif state in success_states:
            break
        
        time.sleep(2)

@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=1)
def download_order(order_url, auth, item_ids, overwrite=True):
    r = requests.get(order_url, auth=auth)
  
    response = r.json()

  
    results = response['_links']['results']
   
   
    
    results_urls = [r['location'] for r in results]
    results_names = [r['name'] for r in results]
    
    
    results_paths = [pathlib.Path(os.path.join('/tmp', n)) for n in results_names]
    
    scenes = {}
    
    for url, name, path in zip(results_urls, results_names, results_paths):
        item_id = list(filter(lambda i: i in name, item_ids))
        if len(item_id) == 0:
            pass
        else:
            item_id = item_id[0]
            if item_id not in scenes:
                scenes[item_id] = {}
            asset_suffix = name.split(f'{item_id}_')[1]
            scenes[item_id][asset_suffix] = path
            if overwrite or not path.exists():
                print('downloading {} to {}'.format(name, path))
                r = requests.get(url, allow_redirects=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                open(path, 'wb').write(r.content)
            else:
                print('{} already exists, skipping {}'.format(path, name))
    return scenes
#@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def clip_and_download(clip_aoi, item_ids, item_type, asset_types, api_key, order_id=None):
    
    # set up requests to work with api
    auth = HTTPBasicAuth(api_key, '')
    
    if order_id is None:
        single_product = [
        {
          "item_ids": item_ids,
          "item_type": item_type,
          "product_bundle": "analytic"
        }]

        # define the clip tool
        clip = {
            "clip": {
                "aoi": clip_aoi
            }
        }
        # create an order request with the clipping tool
        request_clip = {
          "name": "just clip",
          "products": single_product,
          "tools": [clip]
        }
        clip_order_url = place_order(request_clip, auth)
    else:
        orders_url = 'https://api.planet.com/compute/ops/orders/v2'
        clip_order_url = orders_url + '/' + order_id

    poll_for_success(clip_order_url, auth)
    
    return download_order(clip_order_url, auth, item_ids)
    

class IngestJob(object):
    """
        Tool to facilitate data ingestion from Planet Labs to Descartes Labs
    """
    def __init__(self,  aoi, 
                 item_type=ItemType.PSScene4Band,
                 product_id=None,
                 title=None,
                 description=None,
                 overwrite=False,
                 start_datetime=None,
                 end_datetime=None,
                 cloud_fraction=1,
                 limit=None,
                 order_id=None,
                 api_key=None):
        
        self._planet = p.ClientV1(api_key=api_key)
        self._catalog = dl.Catalog()
        self._metadata = dl.Metadata()
        self._auth = dl.Auth()
        self._order_id = order_id
        self._title=title
        self._description=description
        self.stats = None
        self._running = False
        self._items = []
        self.uploads = []
        
        
        if self._running:
            raise Exception('Already processing')
        else:
            self._running = True
            
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._cloud_fraction = cloud_fraction
        self._limit =limit
       
        self._get_items(aoi, [item_type.name])
        self._init_product(product_id, item_type=item_type, overwrite=overwrite)
       
        item_ids = [item['id'] for item in self._items]
        
        scenes = clip_and_download(aoi, item_ids, item_type.name, item_type.bundle, api_key, order_id=self._order_id)
        for scene_id, scene in scenes.items():
                
            
                with open(scene['metadata.json']) as meta_file:
                    metadata = json.load(meta_file)['properties']
                
                with open(scene['3B_AnalyticMS_metadata_clip.xml']) as xml_file:
                    xml_meta = xmltodict.parse(xml_file.read())
                for band in xml_meta['ps:EarthObservation']['gml:resultOf']['ps:EarthObservationResult']['ps:bandSpecificMetadata']:
                    metadata[f"band_{band['ps:bandNumber']}_radiometricScaleFactor"] = band['ps:radiometricScaleFactor']
                    metadata[f"band_{band['ps:bandNumber']}_reflectanceCoefficient"] = band['ps:reflectanceCoefficient']
                
                self._upload_image([str(scene[str(file_key)]) for file_key in item_type.files] , metadata, scene_id)
    def _create_bands(self, item_type):
        if item_type is not None:
            for band_kwargs in item_type.bands:
                band_kwargs['product_id'] = self._product_id
                band = dl.catalog.SpectralBand(**band_kwargs)
                band.save()
        else:
            for srcband in range(1,num_bands+1):
                name = input(f'What is the name of the band at index {srcband}?')
                dtype = input(f'What is the data type of the band at index {srcband}?')
                band_type = input(f'What is type of data does band {srcband} represent (spectral, class, derived)?')
                data_range = list(map(float,input(f'What is the data range of the band at index {srcband}?').split(',')))
                default_range = list(map(float,input(f'What is the default scaling range of the band at index {srcband}?').split(',')))
                physical_range = list(map(float,input(f'What is the value range the band at index {srcband} represents?').split(',')))
                band = dl.catalog.SpectralBand(
                    product_id=product_id, 
                    name=name, data_type=dtype, 
                    band_index=srcband, 
                    data_range=data_range, 
                    physical_range = physical_range, 
                    type=band_type, 
                    default_range=default_range)
    def _create_product(self, item_type):
        title = self._title or input('Enter a product title:')
        description = self._description or input('Enter a product description:')
        product = dl.catalog.Product()
        product.id = self._product_id
        product.name = title
        product.description = description
        product.save()
                
        self._create_bands(item_type)
                
    def _init_product(self, product_id, item_type=None, overwrite=False):
        org = dl.Auth().payload['org']
        self._product_id = f'{org}:{product_id}'
        try:
            product = dl.catalog.Product.get(self._product_id)
            if product is None:
                raise NotFoundError()
            else: 
                if overwrite:  
                    print(f'Overwriting {self._product_id}')
                    print(f'Deleting existing objects...')
                    delete_task = product.delete_related_objects()
                    if delete_task is not None:
                        delete_task.wait_for_completion()
                    product.delete() 
                    self._create_product(item_type)
                else:
                    print(f'Appending images to {self._product_id}')
                   
                                                          
        except NotFoundError:
            self._create_product(item_type)
                    
    def _upload_image(self, paths, planet_properties, scene_id):
        
        print(f'Uploading {paths} to {self._product_id} ...')
        dl_properties = {key: planet_properties[key] for key in planet_properties.keys() & dl.catalog.Image.__dict__.keys()}
        dl_properties['extra_properties'] = planet_properties
        for key, val in  dl_properties['extra_properties'].items():
            if type(val) == bool:
                dl_properties['extra_properties'][key] = str(val).lower()
           
        print(dl_properties)
        img = dl.catalog.Image(**dl_properties)
        img.product_id = self._product_id
        img.id = f'{self._product_id}:{scene_id}'
        
        upload = img.upload([os.path.join(path) for path in paths])
        upload.wait_for_completion()
        print(f'Uploaded {paths} to {self._product_id}. ')
        
        
    def _get_items(self, aoi, item_types):
            
        # build a filter for the AOI
        query = p.filters.and_filter(
            p.filters.geom_filter(aoi),
            p.filters.date_range('acquired', gt=self._start_datetime),
            p.filters.date_range('acquired', lt=self._end_datetime),
             p.filters.range_filter('cloud_cover', lt=self._cloud_fraction)
        )

        request = p.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self._planet.quick_search(request)

        # items_iter returns an iterator over API response pages
        self._items = [i for i in results.items_iter(self._limit)]

    