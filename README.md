# curt-rustled
Basic remote interactive tool with survey module 

## Demo

Cycle 8: https://www.youtube.com/watch?v=NBhoRoCX9go

Cycle 10: https://youtu.be/FhjnRRwlPsM 

## Description

For DSU CSC842 - Security Tools Cycle 8 and Cycle 10

Wrapper for SSH interarctions for Linux and WinRM interactions for Windows with a survey module

## Prerequisties

- python 3.8 or higher
- paramiko
- pywinrm
  
## Installation

  - git clone https://github.com/ac0mm/curt-rustled.git

## Usage

python3 curt_rustled.py

Select WinRM or SSH and follow the prompts

## Three Main Points

- Script interactions with remote hosts
- Survey the remote host to determine current status and potential privilege escalation vectors
- Gracefully close connections

## Why I am Interested

As with previous projects I am interested in providing tools that ensure interactions with a remote host are logged so potential artificats created can be addressed at the end of an assessment. Curt_rustled.py reflects my latest standalone tool that will be used to tweak my greta c2 framework and eventually rolled up into it. For this tool I made the logging a separate file that can now easily be ported and reused by my other projects.

# Areas of Improvement

- Investigate additional SSH key headers for inclusion in the ssh section
- Better capture of output for common commands, such as process list, netstat, directory listings
- upload and download
- traffic redirection
