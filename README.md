## Notes from a dream

How to build an AI
* Google clips: important moments
* Motion track, object recognition
* Movie audio -> ASR + review or subtitled dialogs: train language model for good moment
* Knowledge graph: link pic+words
* Reinforce learning: update network with verbol interaction

## Provisional ideas

- memory/knowledge/concept generation
	- visual: [automatic photography with google clips](https://ai.googleblog.com/2018/05/automatic-photography-with-google-clips.html)
	- audio: use ASR to convert to NLP problem first

- some intuition to neural network
	- [spiking neural network](https://en.wikipedia.org/wiki/Spiking_neural_network): add memory/time to neuron
	- knowledge graph/model checkpoint as output
	- output ensembled from a 'random' selection of sub neural nets
	- ~~kernel output with a distribution (upscaling kernel): adding degenerecy to neighbor neuron $y_{ij}^l = \Sum_{a=0}^{m-1} \Sum_{b=0}^{m-1} \omega_{ab} \sigma(x_{(i+a)(j+b)}^l)$~~  unnecessary, equivilent to add additional convolutional layer

- mind-blasting
	- random firing: all necessary weights can be random initialized, just need to activate the 'right' neuron and reinforce during the training