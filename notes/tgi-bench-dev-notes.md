# TGI bench notes

## Creating enroot container

```
enroot import docker://ghcr.io#huggingface/text-generation-inference:1.0.1
enroot create --name tgi-1.0.1 huggingface+text-generation-inference+1.0.1.sqsh
```
### Crete Bundle
```
enroot bundle -o tgi-1.0.1.run  huggingface+text-generation-inference+1.0.1.sqsh
```

## Start the container

```
export HUGGING_FACE_HUB_TOKEN=< your HF token >
enroot start --rw --root --env HUGGING_FACE_HUB_TOKEN --mount .:/data tgi-1.0.1  --model-id "meta-llama/Llama-2-70b-chat-hf" --num-shard 4 --port 8088 --hostname 172.17.167.1 --trust-remote-code
```

The first run download time for llama-2-70b-chat-hf is around 35min on a gigabit connection. It will be cached in PWD but we will need to store this locally and rsync it over for benchmark runs.

It gives a nice message about setting the revision. I'll do that...
```
2023-08-16T21:14:30.180890Z  WARN text_generation_router: router/src/main.rs:345: `--revision` is not set
2023-08-16T21:14:30.180907Z  WARN text_generation_router: router/src/main.rs:346: We strongly advise to set it to a known supported commit.
2023-08-16T21:14:30.470511Z  INFO text_generation_router: router/src/main.rs:367: Serving revision 36d9a7388cc80e5f4b3e9701ca2f250d21a96c30 
```

### Starting from container bundle .run file (tgi-1.0.1.run)

```
./tgi-1.0.1.run --rw --root --env HUGGING_FACE_HUB_TOKEN --mount .:/data --  --model-id "meta-llama/Llama-2-70b-chat-hf" --num-shard 4 --port 8088 --hostname 172.17.167.1 --trust-remote-code
```

## This client.py should be (mostly) repeatable for benchmarking.

Very useful site for LLM input templates!
[https://gpus.llm-utils.org/llama-2-prompt-template/](https://gpus.llm-utils.org/llama-2-prompt-template/)
```
#!/usr/bin/env python

from text_generation import Client
import time

client = Client("http://172.17.167.1:8088", timeout=40)


prompt = f"""
<s>[INST] <<SYS>>
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information. Instead, say that you don't know the answer.
<</SYS>>

Who is Robert Oppenheimer? [/INST]

"""

# time the inference
start = time.time()

print(
    client.generate(
        f"{prompt}", temperature=0.95, top_k=1, top_p=0.9, max_new_tokens=500
    ).generated_text
)
```

## Create a python env for the client inside a container bundle
This will allow for different client python code to be used for benchmarking different models and prompts.

```
enroot import docker://continuumio/miniconda3
enroot create --name python-client-env continuumio+miniconda3.sqsh
enroot start --rw --root python-client-env
pip install text-generation
```
 NOPE! Good idea but it wont work right!

 ## Create a python env for the client using micromamba

py-client-env.yml
 ```
name: py-client-env
channels:
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
      - text-generation
      - pandas
 ```

 Used my nodepyenv.py program and the above yml file to create a python env for the client.

 python path is `./mm/envs/py-client-env/bin/python`

 ## Modify TGI container to allow a bash shell
 Very annoying that they didn't allow this! 
 We need to be able to modify the container to include the NVIDIA container toolkit 
 so that it is not a runtime install dependency. 

 Creating a new container bundle with the following changes to the the rc config.

 ```
 enroot create --name tgi-1.0.1-2 huggingface+text-generation-inference+1.0.1.sqsh
 cd ~/.local/share/enroot/tgi-1.0.1-2/etc
 ```
 #### current rc file
 ```
 mkdir -p "/usr/src" 2> /dev/null
cd "/usr/src" && unset OLDPWD || exit 1

if [ -s /etc/rc.local ]; then
    . /etc/rc.local
fi

if [ $# -gt 0 ]; then
    exec 'text-generation-launcher' "$@"
else
    exec 'text-generation-launcher' '--json-output'
fi
```
#### change to 
```
mkdir -p "/usr/src" 2> /dev/null
cd "/usr/src" && unset OLDPWD || exit 1

if [ -s /etc/rc.local ]; then
    . /etc/rc.local
fi

if [ $# -gt 0 ]; then
    exec 'text-generation-launcher' "$@"
else
    exec '/bin/bash'
fi
```
#### start the container and install nvidia container toolkit
```
enroot start --rw --root tgi-1.0.1-2
```
Add an editor! (running as root so no sudo)
```
apt update
apt install nano
```
Install nvidia container toolkit
```
Create a script with
```
  DIST=$(
    . /etc/os-release
    echo $ID$VERSION_ID
  )
  curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey |  apt-key add -
  curl -s -L https://nvidia.github.io/libnvidia-container/$DIST/libnvidia-container.list |
     tee /etc/apt/sources.list.d/libnvidia-container.list

  apt-get update
  apt-get install --yes libnvidia-container-tools
```
and install the container toolkit.

Now export the container and create a new bundle
```
enroot export tgi-1.0.1-2
enroot bundle -a tgi-1.0.1-2.sqsh
```
This should be a lot more useful!

