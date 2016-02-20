# cci-api

Flask REST API to access custom ESA CCI database.

Acts as an interface to store data from the cci-sort script in a database.

Database configuration is done in config.py.

## Description

The API provides endpoints for experiments, products and files.

Experiments are the top level objects on the [ESA Climate Change Initiative portal](http://cci.esa.int/). At the time of the writing, the list of available experiments is the following:

 - aerosol
 - cloud
 - cmug
 - fire
 - ghg
 - glaciers
 - ice sheets greenland
 - ice sheets antartica
 - land cover
 - ocean colour
 - ozone
 - sea ice
 - sea level
 - sst
 - soil moisture

Experiments contain products, and each product provides data from a certain sensor, resolution, etc.

The procucts consist of files stored on the ESA CCI FTP server.

## Usage

For each endpoint the API provides the following methods:

 - GET (fetch from database)
 - POST (add to database)
 - PUT (update in database)
 - DELETE (delete from database)

Accessing a specific item in database (GET, PUT, DELETE) is done by specifying the id directly as a URL parameter, e.g. `yourapidomain.com/experiment?id=1`. If no id is specified on the GET method, all items are returned.

Additional data required by the POST and PUT methods is provided to the API as a JSON attachment to the request.

All the API outputs are JSON formatted.