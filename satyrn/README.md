# Satyrn API v0.2.2

This is the core codebase for the Satyrn API. Satyrn is developed by the C3 Lab at Northwestern University and is in pre-release alpha. Details about this work are pending publication.

### License

This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn. 
If not, see <https://www.gnu.org/licenses/>.

-----------

The code in this repository stands alone in providing a REST API which can sit behind the Satyrn UX repository.

For an example v0.2.2 config, see the [political-mini/v2-2 directory](https://github.com/nu-c3lab/satyrn-rings/tree/master/political_mini/v2-2) in the [satyrn-rings](https://github.com/nu-c3lab/satyrn-rings/) repo.

# Satyrn API: Getting Set Up
## Prerequisites
1. Install [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

2. Clone this repo to a place of your choosing.


## Setting up the app environment + Running the App
1. cd into the repo directory, create a Conda virtual environment, and load it up. Something like:
```bash
cd satyrn-api
conda create --name satyrn python=3.8
conda activate satyrn
```

2. Pip install the requirements.txt file into that virtual env
```bash
pip install -r requirements.txt
```
If you receive an error while attempting to install `psycopg2`, install it using `conda install psycopg2`, then re-run the requirements installation command above.

3. Follow the instructions in the [env-example.txt](https://github.com/nu-c3lab/satyrn-api/blob/main/env-example.txt) and get those in your env however you see fit (~/.profile or something context based -- for Mac/Linux users, this rules: [direnv.net](https://direnv.net)).

IMPORTANT: These environment variables must be loaded into your terminal/env whenever you run the Satyrn API. If you do not set up an automated method for loading these environment variables, you'll need to manually add them each time start a new terminal session.

4. To ensure that Satyrn has data to query and analyze, you'll need to make sure it has access to a ring. There are a variety of rings available in the [satyrn-rings](https://github.com/nu-c3lab/satyrn-rings/) repo.
To set up the ring, you'll need to make sure the `connectionString` variable is set to the full qualified path to the database. For a local, SQLite database, this will simply be the absolute path to the database on your computer. For remote databases, this will be the connection string with any required credentials.

5. Add the absolute path of one or more rings to the `rings` list in `site.json`.

6. Now start the server. From the top level directory of satyrn-api, run:
```bash
python wsgi.py
```
If you receive an error while loading SQLIte extensions, you may need to comment out `dbapi_conn.load_extension(file_name)` (line 61 of core/RingObjects/RingDataSource.py). This error typically occurs on Macs with M1/M2 chips.

7. To test your setup, you'll need [Postman](https://www.postman.com/downloads/) or equivalent to send requests. Assuming you have the political-mini ring loaded, you can send a `GET` request to `http://127.0.0.1:5000/api/sqr_analysis/20e114c2-ef05-490c-bdd8-f6f271a6733f/1/` with the following JSON body:
```json
{
    "|1|": "(retrieve_entity Contribution)",
    "|2|": "(retrieve_attribute |1| amount)",
    "|3|": "(greaterthan |2| 1002.0)",
    "|4|": "(retrieve_attribute |1| inState)",
    "|5|": "(collect |2| |4| |3|)",
    "|6|": "(return |5|)"
}
```

If you see results, then the Satyrn API is set up!

## API Spec

The API currently supports the following primary views:

1. __/api/__

This is just a basic health check to see if the API is running.

2. __/api/rings/__

This call will return the rings (and the versions) loaded into memory at the current api instance. It should closely mirror the rings that are listed in the `site.json` file that the site utilizes.

3. __/api/sqr_analysis/<ring_id>/1/__

This endpoint takes SQR plans in the body of the request (as JSON) and executes them with the analytics engine.

### SQR Plans and Running Analysis
As part of our platform, we are developing an intermediate representation between language and queries in order to make 
this process easier called the Structured Question Representation (SQR, pronounced seeker). The purpose of this representation
is to be a data and execution agnostic meaning representation for complex, analytic questions. It is a 
graph-based representation that specifies an ordered series of steps to carry out in pursuit of an answer to a 
user’s question. Each node of the graph represents an operation whose output is fed to later steps which require the 
results. In this way, arbitrarily complex plans can be composed to satisfy any information needs of a user. 
This representation can also be easily converted to statements which describe the plan in plain language.
Our platform currently makes use of this representation when generating queries against relational databases, but 
it is possible to use this as a base representation for building SPARQL queries against knowledge graphs as well.

Here is an example of this representation for a question asking "What is the total contribution amount?":

```json
{
    "|1|": "(retrieve_entity Contribution)",
    "|2|": "(retrieve_attribute |1| amount)",
    "|3|": "(sum |2|)",
    "|4|": "(collect |3|)",
    "|5|": "(return |4|)"
}
```

### Unit Tests

From the `tests` directory, run the following:

```bash
python -m unittest test_sqr_analysis.py
```
