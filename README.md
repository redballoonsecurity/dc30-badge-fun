Repository for the source code featured in Red Balloon's DEFCON 30 Badge Fun article.

Includes:
- `ofrak_scripts.py`: Python script with the source code to do the patches described in the article.
- `play_note_sequence.c`: C source code for the Player Piano patch described in the article.
- `shroomscreen.data`: 1-bit image of OFRAK's mushroom mascot, which can replace the badge's existing boot splash screen.

The Python script can be run in an OFRAK Docker image with the command: 
`docker run -it --rm -v <PATH-TO-THIS-DIRECTORY>:/project --entrypoint bash <OFRAK-DOCKER-IMAGE-NAME> -c "cd /project && python3 ofrak_scripts.py"`
