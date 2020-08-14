# gpt2-discordbot
A discord bot that does natural conversations using gpt-2

## Setup
In google Colab, run the code below with your bot token and training file as either a txt file or a directory of txt files.
```
bot_token = ""
training_file=""
from google.colab import drive
drive.mount('/content/drive')
%tensorflow_version 1.x
%cd "drive/My Drive/Colab Notebooks"

!git clone https://github.com/minimaxir/gpt-2-simple.git
%cd "gpt-2-simple"

!git clone https://github.com/K-Kazum1/gpt2-discordbot

!mv gpt2-discordbot/discordbot.py discordbot.py
!mv gpt_2_simple/gpt_2.py gpt_2.py
open("bot.txt",'w').write(bot_token)

import gpt_2 as gpt2
import os,re
model_name="345M"
gpt2.download_gpt2(model_name=model_name)

if training_file != "":
  sess = gpt2.start_tf_sess()
  gpt2.finetune(sess,
              training_file,
              model_name="..",
              steps=-1,print_every=100,restore_from='fresh')
```
              
##Deploying
Every time you want to start up the bot, run the below code in Google Colab.
```
from google.colab import drive
drive.mount('/content/drive')
%tensorflow_version 1.x
import tensorflow as tf

%cd 'drive/My Drive/Colab Notebooks/gpt_2_simple'
!pip install discord
!pip install toposort
!python yonakabot.py
```
