#!/usr/bin/env bash
# Clone the seven expert source repositories (shallow, blobless).
# Reference material only: no weights, no installs, no inference.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p sources && cd sources
repos=(
  jacobye2017-afk/jacob-ye-seedance-prompt
  opensource-works/awesome-seedance-prompts
  Wan-Video/Wan2.2
  ali-vilab/VACE
  KlingTeam/ReCamMaster
  divolleggett/awesome-character-consistency
  harry0703/MoneyPrinterTurbo
)
for r in "${repos[@]}"; do
  n="${r##*/}"
  [ -d "$n" ] && { echo "skip $n"; continue; }
  git clone --depth 1 --filter=blob:none "https://github.com/$r.git" "$n"
done
