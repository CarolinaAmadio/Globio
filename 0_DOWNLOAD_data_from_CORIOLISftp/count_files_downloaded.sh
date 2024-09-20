#!/bin/bash

# Directory da cercare
dir="/g100_work/OGS_devC/camadio/GLOBIO/CORIOLIS"

# Conta i file con estensione .nc nelle sottocartelle
count=$(find "$dir" -type f -name "*.nc" | wc -l)

# Stampa il numero di file
echo "Numero di file .nc trovati: $count"
