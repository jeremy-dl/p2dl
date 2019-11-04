from planet.api import ClientV1
import planet.api as p
import descarteslabs as dl
import os
from descarteslabs.exceptions import NotFoundError
from tempfile import NamedTemporaryFile
import time
import json
import requests
import pathlib
from requests.auth import HTTPBasicAuth
from retrying import retry

from p2dl.ptypes import AssetType, ItemType


# functions for submitting, polling, and downloading an order
@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def place_order(request, auth):
    orders_url = 'https://api.planet.com/compute/ops/orders/v2'
    headers = {'content-type': 'application/json'}
    response = requests.post(orders_url, data=json.dumps(request), auth=auth, headers=headers)
    
    if not response.ok:
        raise Exception(response.content)

    order_id = response.json()['id']
    print(order_id)
    order_url = orders_url + '/' + order_id
    return order_url
@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def poll_for_success(order_url, auth, num_loops=50):
    count = 0
    while(count < num_loops):
        count += 1
       
        r = requests.get(order_url, auth=auth)
        response = r.json()
        state = response['state']
        print(state)
        
        success_states = ['success', 'partial']
        if state == 'failed':
            raise Exception(response)
        elif state in success_states:
            break
        
        time.sleep(10)

@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def download_order(order_url, auth, overwrite=True):
    r = requests.get(order_url, auth=auth)
  
    response = r.json()
  
    results = response['_links']['results']
   
    
    results_urls = [r['location'] for r in results]
    results_names = [r['name'] for r in results]
    results_paths = [pathlib.Path(os.path.join('/tmp', n)) for n in results_names]
    
    files = []
    
    for url, name, path in zip(results_urls, results_names, results_paths):
        if str(path).endswith('AnalyticMS_clip.tif'):
            files.append(path)
            if overwrite or not path.exists():
                print('downloading {} to {}'.format(name, path))
                r = requests.get(url, allow_redirects=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                open(path, 'wb').write(r.content)
            else:
                print('{} already exists, skipping {}'.format(path, name))

    return files
@retry(wait_random_min=1000, wait_random_max=2000, stop_max_attempt_number=7)
def clip_and_download(clip_aoi, item_ids, item_type, asset_type, api_key, order_id=None):
    

    # set up requests to work with api
    auth = HTTPBasicAuth(api_key, '')
    
    if order_id is None:
        single_product = [
        {
          "item_ids": item_ids,
          "item_type": item_type,
          "product_bundle": asset_type
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
    
    downloaded_clip_files = download_order(clip_order_url, auth)
    
    
    for d in downloaded_clip_files:
        yield d

class IngestJob(object):
    """
        Tool to facilitate data ingestion from Planet Labs to Descartes Labs
    """
    def __init__(self,  aoi, 
                 item_type=ItemType.PSScene4Band,
                 product_id=None,
                 asset_type=AssetType.analytic,
                 start_datetime=None,
                 end_datetime=None,
                 limit=None,
                 order_id=None,
                 api_key=None):
        
        self._planet = p.ClientV1(api_key=api_key)
        self._catalog = dl.Catalog()
        self._metadata = dl.Metadata()
        self._auth = dl.Auth()
        self._order_id = order_id
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
        self._limit =limit
       
        self._get_items(aoi, [item_type.name])
        self._init_product(product_id, item_type=item_type)
       
        item_ids = [item['id'] for item in self._items]
        
        print('Ordering and downloading clipped GeoTiff from Planet.')
        
        for clipped_file in clip_and_download(aoi, item_ids, item_type.name, asset_type.name, api_key, order_id=self._order_id):
            
            items = list(filter(lambda i: i['id'] in clipped_file,  self._items))
            item = items[0] if(len(items)>0) else None
                
            
            self._upload_image(clipped_file, item)

    def _init_product(self, product_id, item_type=None):
        self._product_id = f'{self._auth.namespace}:{product_id}'
        try:
            product = self._catalog.get_product(f'{self._auth.namespace}:{product_id}')
            if input(f'{self._auth.namespace}:{product_id} already exists, overwrite or append? [O]a').lower() =='o':
                product_kwargs = product['data']['attributes']
                product_kwargs['product_id'] = product_id
                bands = self._metadata.get_bands_by_product(f'{self._auth.namespace}:{product_id}')
                self._catalog.remove_product(f'{self._auth.namespace}:{product_id}', cascade=True)
                self._catalog.add_product(**product_kwargs)
                for band_id, band in bands.items():
                    band['product_id']=f'{self._auth.namespace}:{product_id}'
                    try:
                        print(band)
                        self._catalog.add_band(**band)
                    except NotFoundError as e:
                        print( e)
                                                 
        except NotFoundError:
            if input(f'Create new product {self._auth.namespace}:{product_id}? [Y]n').lower() == 'y':
                title = input('Enter a product title:')
                description = input('Enter a product description:')
                product_id = self._catalog.add_product(
                    product_id,
                    title,
                    description
                )['data']['id']
                
                if item_type is not None:
                    for band in item_type.bands:
                        band['product_id'] = product_id
                        self._catalog.add_band(**band)
                else:
                    for srcband in range(1,num_bands+1):
                        name = input(f'What is the name of the band at index {srcband}?')
                        dtype = input(f'What is the data type of the band at index {srcband}?')
                        band_type = input(f'What is type of data does band {srcband} represent (spectral, class, derived)?')
                        data_range = list(map(float,input(f'What is the data range of the band at index {srcband}?').split(',')))
                        default_range = list(map(float,input(f'What is the default scaling range of the band at index {srcband}?').split(',')))
                        physical_range = list(map(float,input(f'What is the value range the band at index {srcband} represents?').split(',')))
                        self._catalog.add_band(product_id=product_id, name=name, dtype=dtype, srcband=srcband, data_range=data_range, physical_range = physical_range, type=band_type, default_range=default_range)
                
            else:
                raise Exception('Need a product to write into')
                    
    def _upload_image(self, path, item):
        print(f'Uploading {path} to {self._product_id} ...')
        year = str(path).split('/')[-1][:4]
        month = str(path).split('/')[-1][4:6]
        day =  str(path).split('/')[-1][6:8]
        acquired = f'{year}-{month}-{day}'
        
           
        with open(path, 'rb') as file_to_upload:
            self.uploads.append(
                self._catalog.upload_image(file_to_upload, self._product_id, acquired=acquired))
        print(f'Uploaded {path} to {self._product_id}. ')
        
        
    def _get_items(self, aoi, item_types):
            
        # build a filter for the AOI
        query = p.filters.and_filter(
            p.filters.geom_filter(aoi),
            p.filters.date_range('acquired', gt=self._start_datetime),
            p.filters.date_range('acquired', lt=self._end_datetime)  
        )

        request = p.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self._planet.quick_search(request)

        # items_iter returns an iterator over API response pages
        self._items = results.items_iter(self._limit)

    