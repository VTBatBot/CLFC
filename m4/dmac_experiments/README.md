#### DMAC only allows one simultaneous transfer

- Limitations:

  - Only one DMAC peripheral
  - Only one DMA channel can be active at a time
  - A single descriptor must complete [all of its beats] before moving to the next [descriptor]

- Problem: this causes significant gaps in transfers (`dmac_limitations.ino`)

  - ![1584462278038](https://gist.githubusercontent.com/branw/08755535cdbf2a120071ed6bed8b8f0a/raw/e0379c18707e0ec12aee65b7a737c455a87dbd7d/1584462278038.png)
  - This manifests either when using multiple DAC channels at high frequencies (not important for us), and also when trying to combine ADC and DAC operations (very important for us)
    - The SAMD51 does not seem to support reading/writing multiple buffers at the same time
    - The ADC/DAC peripherals do not have any buffering of their own and rely entirely on DMAC

- Idea: chain a bunch of smaller descriptors (`dmac_splitting.ino`)

  - At 8 divisions:

    ![1584463791168](https://gist.githubusercontent.com/branw/08755535cdbf2a120071ed6bed8b8f0a/raw/e0379c18707e0ec12aee65b7a737c455a87dbd7d/1584463791168.png)

  - At 1024 divisions:

    ![1584464000057](https://gist.githubusercontent.com/branw/08755535cdbf2a120071ed6bed8b8f0a/raw/e0379c18707e0ec12aee65b7a737c455a87dbd7d/1584464000057.png)

  - Problem: this introduces a significant delay proportional to the number of descriptors

    - 4096 samples at 8 divisions (16 descriptors) takes ~412us (~9.9MHz)
    - 4096 samples at 1024 divisions (2048 descriptors) takes ~2.26ms (~1.8MHz)

- Question: is there a way to interleave two descriptors such that beats are done 010101 rather than 000111?

  - ~~Doesn't look like it~~
  - Burst mode!

- Question: how do others do it?

  - [Adafruit's MP3 player uses two DMA channels to achieve stereo DAC output](https://github.com/adafruit/Adafruit_MP3/blob/master/examples/DMA_fancy_player/DMA_fancy_player.ino#L132) (`dmac_burst.ino`)
    - ![1584470088482](https://gist.githubusercontent.com/branw/08755535cdbf2a120071ed6bed8b8f0a/raw/e0379c18707e0ec12aee65b7a737c455a87dbd7d/1584470088482.png)
    - The secret to interleaving channels is burst mode (`CHCTRLA.TRIGACT=BURST`)
      - 4096 samples takes ~4.46ms (~918kHz)
      - Worse performance than chained descriptors, but cleaner output

- Idea: don't use DMAC

  - ???
