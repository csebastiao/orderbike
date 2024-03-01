# OrderBike

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/csebastiao/orderbike)](https://github.com/csebastiao/orderbike/blob/main/LICENSE)

OrderBike is a project where the aim is to find an optimal order of construction for a bicycle network plan. What is optimal is based on what you want to prioritize in your strategy as the final network is fixed. What to prioritize is a moral and political choice that need to be translated into a network metric.

## Bikeplanpic

On the `Bikeplanpic` folder, you will find a non-exhaustive list of images of bicycle network plan of various precision, actually planned or not. The `0_Metadata.md` file list the related informations. Whenever the word datascreen is used instead of picture in the name of an image, it means that the image was apparently made using a GIS software, so a closed or open shapefile should exist.
This folder serves as an inspiration database to see what bicycle network plan look like, in their final form, and in the imagined evolution of them, with a diversity of size, means, topography...

To find examples of networks, see [UrbanToyGraph](https://github.com/csebastiao/UrbanToyGraph) for toy network looking like some typical urban shapes, or [TransportationNetworks](https://github.com/bstabler/TransportationNetworks) for (more or less simplified) urban networks with Origin-Destination-pairs on them, that are usually used for car traffic engineering.

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
