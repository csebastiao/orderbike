# OrderBike

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/csebastiao/orderbike)](https://github.com/csebastiao/orderbike/blob/main/LICENSE)

OrderBike aims to find an optimal order of construction for a bicycle network plan. Optimality is based on the political or moral choice of what aspect to prioritize in the growth strategy. This choice needs to be translated into a network metric.

This source code has been used in the scientific paper [*The Trade-Off between Directness and Coverage in Transport Network Growth*](https://arxiv.org/abs/2507.13005) by Clément Sebastiao, Anastassia Vybornova, Ane Rahbek Vierø, Luca Maria Aiello, and Michael Szell.

**Preprint**: [arXiv:2507.13005](https://arxiv.org/abs/2507.13005)  

## Bikeplanpic

The `Bikeplanpic` folder contains a non-exhaustive list of images of bicycle network plans of varying precision, from actual plan to rough vision. The `0_Metadata.md` file list related information. Whenever the word "datascreen" is used instead of "picture" in the name of an image, it means that the image was apparently made using a GIS software, so a closed or open shapefile should exist. This folder serves as an inspiration for what bicycle network plans look like "in the wild", in both their final form and in their envisaged evolution, with a diversity of sizes, topographies, etc.

For examples of networks, see [UrbanToyGraph](https://github.com/csebastiao/UrbanToyGraph) for stylized urban street networks, or [TransportationNetworks](https://github.com/bstabler/TransportationNetworks) for (more or less simplified) urban networks with Origin-Destination-pairs on them that are usually used for car traffic engineering. Another option is to use real street networks from [OpenStreetMap](https://www.openstreetmap.org) using [OSMnx](https://github.com/gboeing/osmnx).

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

To find an order of growth, you need to define a networkx Graph object that is your bicycle network plan, where every edge has a boolean attribute named `built` to distinguish the part of the network that is already built and the one that is planned. Once you have your network ready, you need to choose a set of constraints on the growth, and a growth strategy. Orderbike then determines an order of construction that can be visualized and analyzed through premade functions.

To apply different growth functions in multiple predetermined stages, use one growth function on the final graph after the first stage, then use another growth function on the final graph after the second stage with the built part taken from the first stage, until reaching the last stage. To optimize on different metrics based on reaching some specific values, either create a new dynamic metric function that changes through time, or launch at start the growth with a first function, then relaunch it with another function that takes the first N steps from the first growth order marked as built.


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

You can put as keyword arguments everything that is processed by the precomputation function. For an example using everything, see `orderbike.metrics.growth_coverage` and `orderbike.metrics.precomp_growth_coverage`. If you don't need a precomputation function, the `**kwargs` provided to the growth function will be provided to the metric function instead. The `metricname` function needs to return a single value, being the value of the metric for the step with this specific edge removal/addition. It needs to be something where the maximum value is pointing to the optimal choice. So if the actual metric is a monotonic function in the number of steps, like coverage, you need to make a difference betweeen subtractive and additive order in the growth function based on that metric (see `orderbike.metrics.growth_coverage`).

### Ranking function
To add a ranking metric, you need to respect the following template:

```python
def rankingname(G, keyword_arg=0):
  """Here G is the final graph."""
  rank = ...
  return rank
```

The `rankingname` function needs to return a list of edges in descending order.

## Credits

Please cite as: 
>C. Sebastiao, A. Vybornova, A.R. Vierø, L.M. Aiello, M. Szell. The Trade-Off between Directness and Coverage in Transport Network Growth. arXiv preprint arXiv:2507.13005 (2025)

Development of OrderBike was supported by the Horizon Europe grant JUST STREETS (Grant agreement ID: 101104240).