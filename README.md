# whisper-timestamped

Multilingual Automatic Speech Recognition with word-level timestamps and confidence.

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
   * [Python](#python)
   * [Command line](#command-line)
   * [Plotting word alignment](#plotting-word-alignment)
   * [Example output](#example-output)
* [Acknowlegment](#acknowlegment)
* [Citations](#citations)

## Description
[Whisper](https://openai.com/blog/whisper/) is a set of multi-lingual robust speech recognition models, trained by OpenAI,
that achieve state-of-the-art in many languages.
Whisper models were trained to predict approximative timestamps on speech segments (most of the times with 1 sec accuracy),
but cannot originally predict word timestamps.
This repository proposes an implementation to **predict word timestamps, and give more accurate estimation of speech segments, when transcribing with Whipser models**.
Besides, a confidence score is assigned to each word and each segment (both computed as "exp(mean(log probas))" on the probabilities of subword tokens).

The approach is based on approach Dynamic Time Warping (DTW) applied to cross-attention weights,
as done by [this notebook by Jong Wook Kim](https://github.com/openai/whisper/blob/f82bc59f5ea234d4b97fb2860842ed38519f7e65/notebooks/Multilingual_ASR.ipynb).
There are some additions to this notebook:
* The start/end estimation is more accurate
* **If possible (without beam search...), there no additional inference steps are required to predict word timestamps** (word alignment is done on the fly, after each speech segment is decoded).
* There is a special care about memory usage: `whisper-timestamped` is able to process long files, with little additional memory with respect to the regular use of Whisper model.

### Note on other approaches

Another relevant approach to recover word-level timestamps consists in using wav2vec models that predict characters,
as successfully implemented in [whisperX](https://github.com/m-bain/whisperX).
But these approaches have several drawbacks, which does not have approaches based on cross-attention weights such as `whisper_timestamped`.
These drawbacks are:
* The need to perform twice the inference (once with Whisper, once with wav2vec), which has an impact on the Real Time Factor.
* The need to handle (at least) an additional neural network, which consumes memory.
* The need to find one wav2vec model per language to support.
* The need to normalize characters in whisper transcription to match the character set of wav2vec model.
This involves awkward language-dependent conversions, like converting numbers to words ("2" -> "two"), symbols to words ("%" -> "percent", "€" -> "euro(s)")...
* The lack of robustness around speech disfluencies (fillers, hesitations, repeated words...) that are usually removed by Whisper.

## Installation

Requirements:
* `python3` (version higher or equal to 3.7, at least 3.9 is recommended)
* `ffmpeg` (see instructions for installation on the [whisper repository](https://github.com/openai/whisper)

You can install `whisper-timestamped` either by using pip:
```bash
pip3 install git+https://github.com/linto-ai/whisper-timestamped
```
or by cloning this repository and running installation:
```bash
git clone https://github.com/linto-ai/whisper-timestamped
cd whisper-timestamped/
python3 setup.py install
```

If you want to plot alignement between audio timestamps and words (as in [this section](#plotting-word-alignment)), you also need matplotlib
```bash
pip3 install matplotlib
```

## Usage

### Python

In python, you can use the function `whisper_timestamped.transcribe()` that is similar to the fonction `whisper.transcribe()`
```python
import whisper_timestamped
help(whisper_timestamped.transcribe)
```
The main differences with `whisper.transcribe()` are:
* The output will include a key `"words"` for all segments, with the word start and end position. Note that word will include punctuation. See example [below](#example-output).
* By default, all options that require several steps of decoding are disabled, in favour of an efficient decoding strategy.
  Use ```beam_size=5, best_of=5, temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)``` for Whisper default.

In general, by importing `whisper_timestamped` instead of `whisper` in your python script, it should do the job, if you use `transcribe(model, ...)` instead of `model.transcribe(...)`:
```
import whisper_timestamped as whisper

audio = whisper.load_audio("AUDIO.wav")

model = whisper.load_model("tiny", device="cpu")

result = whisper.transcribe(model, audio, language="fr")

import json
print(json.dumps(result, indent = 2, ensure_ascii = False))
```

### Command line

You can also use `whisper_timestamped` on the command line, similarly to `whisper`. See help with:
```bash
whisper_timestamped --help
```

The main differences with `whisper` CLI are:
* The output JSON contains word timestamps and confidence scores. See example [below](#example-output).
* There is an additional CSV output format
* For SRT, VTT, TSV formats, there will be additional files saved with word timestamps
* By default, no output folder is set: Use `--output_dir .` for Whisper default
* By default, all options that require several steps of decoding are disabled, in favour of an efficient decoding strategy.
  Use ```--accurate``` for Whisper default (which is an alias for ```--beam_search 5 --temperature_increment_on_fallback 0.2 --best_of 5```)

An example command line to process several files with the `tiny` model and output results in the current folder as whisper would do by default:
```
whisper_timestamped audio1.flac audio2.mp3 audio3.wav --model tiny --accurate --output_dir .
```

### Plot of word alignment

Note that you can use option `plot_word_alignment` of python function `whisper_timestamped.transcribe()`, or option `--plot` of `whisper_timestamped` CLI in order to see the word alignment for each segment.
The upper plot represents the transformation of cross-attention weights that is used for DTW;
The lower plot is a MFCC representation of the input signal (features used by Whisper).

![Example alignement](figs/example_alignement_plot.png)

### Example output

Here is an example output of `whisper_timestamped.transcribe()`, that can be seen by using CLI
```bash
whisper_timestamped AUDIO_FILE.wav --model tiny --language fr
```
```json
{
  "text": " Bonjour! Est-ce que vous allez bien?",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.5,
      "end": 1.2,
      "text": " Bonjour!",
      "tokens": [ 25431, 2298 ],
      "temperature": 0.0,
      "avg_logprob": -0.6674491882324218,
      "compression_ratio": 0.8181818181818182,
      "no_speech_prob": 0.10241222381591797,
      "confidence": 0.51,
      "words": [
        {
          "text": "Bonjour!",
          "start": 0.5,
          "end": 1.2,
          "confidence": 0.51
        }
      ]
    },
    {
      "id": 1,
      "seek": 200,
      "start": 2.02,
      "end": 4.48,
      "text": " Est-ce que vous allez bien?",
      "tokens": [ 50364, 4410, 12, 384, 631, 2630, 18146, 3610, 2506, 50464 ],
      "temperature": 0.0,
      "avg_logprob": -0.43492694334550336,
      "compression_ratio": 0.7714285714285715,
      "no_speech_prob": 0.06502953916788101,
      "confidence": 0.595,
      "words": [
        {
          "text": "Est-ce",
          "start": 2.02,
          "end": 3.78,
          "confidence": 0.441
        },
        {
          "text": "que",
          "start": 3.78,
          "end": 3.84,
          "confidence": 0.948
        },
        {
          "text": "vous",
          "start": 3.84,
          "end": 4.0,
          "confidence": 0.935
        },
        {
          "text": "allez",
          "start": 4.0,
          "end": 4.14,
          "confidence": 0.347
        },
        {
          "text": "bien?",
          "start": 4.14,
          "end": 4.48,
          "confidence": 0.998
        }
      ]
    }
  ],
  "language": "fr"
}
```

## Acknowlegment
* [whisper](https://github.com/openai/whisper): Whisper speech recognition (License MIT).
* [dtw-python](https://pypi.org/project/dtw-python): Dynamic Time Warping (License GPL v3).

## Citations
If you use this in your research, just cite the repo,

```bibtex
@misc{lintoai2023whispertimestamped,
  title={whisper-timestamped},
  author={Louradour, J{\'e}r{\^o}me},
  journal={GitHub repository},
  year={2023},
  publisher={GitHub},
  howpublished = {\url{https://github.com/linto-ai/whisper-timestamped}}
}
```

as well as OpenAI Whisper paper,

```bibtex
@article{radford2022robust,
  title={Robust speech recognition via large-scale weak supervision},
  author={Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  journal={arXiv preprint arXiv:2212.04356},
  year={2022}
}
```

and this paper for Dynamic-Time-Warping

```bibtex
@article{JSSv031i07,
  title={Computing and Visualizing Dynamic Time Warping Alignments in R: The dtw Package},
  author={Giorgino, Toni},
  journal={Journal of Statistical Software},
  year={2009},
  volume={31},
  number={7},
  doi={10.18637/jss.v031.i07}
}
```
