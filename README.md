# OrderBike

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/csebastiao/orderbike)](https://github.com/csebastiao/orderbike/blob/main/LICENSE)

OrderBike is a project where the aim is to find an optimal order of construction for a bicycle network plan. What is optimal is based on what you want to prioritize in your strategy as the final network is fixed. What to prioritize is a moral and political choice that need to be translated into a network metric.

## Bikeplanpic

On the `Bikeplanpic` folder, you will find a non-exhaustive list of images of bicycle network plan of various precision, actually planned or not. The `0_Metadata.md` file list the related informations. Whenever the word datascreen is used instead of picture in the name of an image, it means that the image was apparently made using a GIS software, so a closed or open shapefile should exist.
This folder serves as an inspiration database to see what bicycle network plan look like, in their final form, and in the imagined evolution of them, with a diversity of size, means, topography...

To find examples of networks, see [UrbanToyGraph](https://github.com/csebastiao/UrbanToyGraph) for toy network looking like some typical urban shapes, or [TransportationNetworks](https://github.com/bstabler/TransportationNetworks) for (more or less simplified) urban networks with Origin-Destination-pairs on them, that are usually used for car traffic engineering. Another option is to use real street network from [OpenStreetMap](https://www.openstreetmap.org) using [OSMnx](https://github.com/gboeing/osmnx).

## Installation of OrderBike

First clone the repository in the folder of your choosing:

```
git clone https://github.com/csebastiao/orderbike.git
```

Locate yourself within the cloned folder, and create a new virtual environment. You can either create a new virtual environment then install the necessary dependencies with `pip` using the `requirements.txt` file:

```
pip install -r requirements.txt
```

Or create a new environment with the dependencies with `conda` or `mamba` using the `environment.yml` file:

```
mamba env create -f environment.yml
```

Once your environment is ready, you can locally install the package using:

```
pip install -e .
```

## How to use

To find an order of growth, you need to define a networkx Graph object that is your bicycle network plan, with on every edge a boolean attribute named `built` to discriminate the part of the network that is already built and the one that is planned. Once you have your network, you need to choose a set of constraints on the growth, and a growth strategy. You then get an order of construction, that can be visualized and analyzed through premade functions.

If you want to make the growth in multiple determined stages, you can simply use the growth function on the final graph after the first stage, then use the growth function on the final graph after the second stage with as built part the first stage, until reaching the last stage. If you want to optimize on different metrics based on reaching some specific values, you can either create a new dynamic metric function changing through time, or you can launch a first time the growth with the first metric on which to optimize, and relaunch it with another metric with the first N steps of the first growth order selected as built.


## Add your own functions for the growth

### Dynamic metric function
To add a dynamic metric, you need to respect the following template:

```python
def metricname(G, edge, keyword_arg=0):
  """Here G is the one with the removed or added edge, also given here as edge. The kwargs come from the results of the precomp_metricname."""
  compute_something = ...
  return compute_something

def precomp_metricname(G, order="subtractive", keyword_arg=0):
  """Here G is the actual one, before the test of adding/removing one depending on the order of the greedy optimization, also given here as order. The kwargs given in the order_growth function will go here."""
  if order == "subtractive":
    compute_something = ...
  elif order == "additive":
    compute_something = ...
  return {"keyword_arg_0": compute_something}
```

Remember that you can put as keyword arguments everything that come through the precomputation function, that can be useful. For an example using everything, see `orderbike.metrics.growth_coverage` and `orderbike.metrics.precomp_growth_coverage`. If you don't need a precomputation function, the `**kwargs` given to the growth function will be given to the metric function instead. The `metricname` function need to return a single value, being the value of the metric for the step with this specific edge removal/addition. It needs to be something where the maximum value is pointing to the optimal choice. So if the actual metric is a monotonic function of the number of step like coverage, you need to make a difference betweeen subtractive and additive order in the growth function based on that metric (see `orderbike.metrics.growth_coverage`).

### Ranking function
To add a ranking metric, you need to respect the following template:

```python
def rankingname(G, keyword_arg=0):
  """Here G is the final graph."""
  rank = ...
  return rank
```

The `rankingname` function need to return a list of edges in descending order.
