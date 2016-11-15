#!/usr/bin/env bash

rethinkdb restore --force pkmntcgdb_sample.tar.gz
python3 create_indexes.py
