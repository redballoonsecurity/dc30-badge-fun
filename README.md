Repository for the source code featured in [Red Balloon's DEFCON 30 Badge Fun
article](https://redballoonsecurity.com/def-con-30-badge-fun-with-ofrak/index.html).
The firmware modification is performed using [OFRAK, our newly-released binary
analysis and modification framework](https://ofrak.com/).

Includes:

- [`ofrak_scripts.py`](ofrak_scripts.py): Python script with the source code to
  perform the patches described in the article
- [`play_note_sequence.c`](play_note_sequence.c): C source code for the player
  piano patch described in the article
- [`shroomscreen.data`](shroomscreen.data): 1-bit image of OFRAK's mushroom
  mascot, which can replace the badge's existing boot splash screen

The included Python script can be run in an OFRAK Docker container with the command: 

``` bash
docker run \
  --interactive \
  --tty \
  --rm \
  --volume "$(pwd)":/project \
  --entrypoint bash -c "cd /project && python3 ofrak_scripts.py" \
  redballoonsecurity/ofrak/ghidra:latest  # Swap this out if using a different OFRAK Docker image
```
