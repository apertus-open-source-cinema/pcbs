# apertus pcbs
This generates artefacts (gerbers, etc.) for the eagle based PCBs of the apertus project. 
Currently it generates
- a zip with gerbers for the [4 layer oshpark process](https://docs.oshpark.com/services/four-layer/)
- (searchable) PDFs of the schematic
- preview images of the boards
- a [webpage](https://apertus-open-source-cinema.github.io/pcbs) that displays these artefacts grouped by board versions and variants
## Process
Generating these artefacts is a multi step process. First the board and schematic files located in the `boards` folder are analyzed to determine license and copyright information from the silkscreen and schematic annotations. This will generate `.license` files for each board and schematic file that does not already have one. To run this steps use 
```sh
python3 analyze.py
```
Please check the extracted information for correctness and fix any errors found before commiting the `.license` file.

The next step of the process is the collection of all the PCB versions, variants and assembly variants. This is done by running
``` sh
python3 generate_info.py
```
This creates `info.json` containing all the infos.

Now the gerbers, schematic PDFs and preview images are generated. For this step EAGLE version 7 needs to be installed. Running
``` sh
python3 gen.py
```
will then generate them. This can take very long depending on the number of cpu cores.

Finally the webpage displaying and providing download links can be generated. For this the preview first images need to be converted from PNG to WebP. This can for example be done with

``` sh
find boards -name '*.png' | parallel -j100% cwebp -lossless {} -o {.}.webp
```

Then the webpage can be built:
``` sh
cd web && npm run build
```
Note that this will generate a webpage for deployment at https://apertus-open-source-cinema.github.io/pcbs/. For local development you can use
``` sh
cd web && npm install && parcel serve src/index.html
```
## CI setup
The CI does almost the same steps as described above. It uses a docker container generated using
``` sh
$(nix-build --no-out-link docker_image.nix) | docker load
```
to run the steps depending on eagle and furthermore uses `xvfb-run` to avoid the need of an actual X11 server.

Finally it splits the `gen.py` step into multiple shards that are run in parallel across multiple workers, as a single worker can not finish under the `6h` time limit.
## Adding PCBs
To add a new PCB simply drop the pair of `.sch` and `.brd` files in the `boards` folder followed by running 
```sh 
python analyze.py
```
and fixing / manually adding the `.license` files.
